from time import time
from typing import Callable, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from ..containers import EEGContainer, EventContainer
from ..devices.base import DeviceBase
from ..feature_extraction import *
from ..preprocessing import PreprocessingPipeline
from ..tasks.base import PersistentTaskBase
from ..utils import osum
from ..utils.logging import AuthLogger
from .auth_exception import AuthException
from .operation_modes import SimilarityMode, TemplateMode
from .template_database import TemplateDatabase


class KeyWave():
    def __init__(self,
                 device: DeviceBase,
                 task: PersistentTaskBase,
                 preprocessing_pipeline: PreprocessingPipeline,
                 feature_extraction: FeatureExtractionModelBase,
                 database: TemplateDatabase,
                 similarity_metric: Callable[[NDArray,
                                              NDArray],
                                             float],
                 default_threshold: float,
                 logging_directory: str = "log",
                 before_event_time_ms: int = 200,
                 after_event_time_ms: int = 800,
                 template_mode: TemplateMode = TemplateMode.AverageTemplate,
                 similarity_mode: SimilarityMode = SimilarityMode.AverageSimilarity) -> None:
        """Constructor for KeyWave verification system. A prototype brainwave-based verification system based on ERPs.
        KeyWave supports a continuous authentication mode, in which a person is first authenticated or identified using their brainwaves.
        Following this, the person's BCI is effectively transformed into a hardware token that continuously proves the user's identity.
        This hardware token expires as soon as the BCI is either removed from the person's head or the person performs excessive movement.

        :param device: Device to be used for enrollment, authentication, and verification. The device is further used as a token in case of continuous authentication.
        :type device: DeviceBase
        :param task: ERP acquisition task used to collect data necessary for enrollment, authentication, and verification
        :type task: PersistentTaskBase
        :param preprocessing_pipeline: Pipeline to be applied to recorded data
        :type preprocessing_pipeline: PreprocessingPipeline
        :param feature_extraction: Model to be used for feature extraction
        :type feature_extraction: FeatureExtractionModelBase
        :param database: Database object where recorded templates and IDs are stored. To recover a previous state, supply KeyWave with the same database. All persistent states are stored inside the database except for the continuous authentication state.
        :type database: TemplateDatabase
        :param similarity_metric: Similarity metric to be used to determine the similarity between two recordings
        :type similarity_metric: Callable[[NDArray, NDArray], float]
        :param default_threshold: Minimum similarity threshold between two samples to be considered equal
        :type default_threshold: float
        :param logging_directory: Directory for logging, defaults to "log"
        :type logging_directory: str, optional
        :param before_event_time_ms: Time before stimulus to be considered for ERP extraction defaults to 200
        :type before_event_time_ms: int, optional
        :param after_event_time_ms: Time after the stimulus to be considered for ERP extraction defaults to 800
        :type after_event_time_ms: int, optional
        :param template_mode: Template creation mode, defaults to TemplateMode.AverageAndSingleTemplates
        :type template_mode: TemplateMode, optional
        :param similarity_mode: Similarity mode for multiple samples defaults to SimilarityMode.AverageSimilarity
        :type similarity_mode: SimilarityMode, optional
        """
        assert isinstance(device, DeviceBase)
        assert isinstance(preprocessing_pipeline, PreprocessingPipeline)
        assert isinstance(task, PersistentTaskBase)
        assert isinstance(database, TemplateDatabase)

        self.device = device
        self.preprocessing_pipeline = preprocessing_pipeline
        self.task = task
        self.database = database
        self.feature_extraction = feature_extraction
        self.similarity_metric = similarity_metric
        self.default_threshold = default_threshold
        self.logger = AuthLogger(logging_directory)
        self.last_auth = 0
        self.last_id = None
        self.before_event_time_ms = before_event_time_ms
        self.after_event_time_ms = after_event_time_ms
        self.template_mode = template_mode
        self.similarity_mode = similarity_mode

    def reset(self):
        """Resets system to initial state. Should be done if continuous authentication is being used.
        """
        self.last_id = None
        self.last_auth = 0

    def configure_logging(self, event_logging: bool, file_logging: bool):
        """Configure logging behavior for authentication system.

        :param event_logging: If set to true, system performs logging. Else not.
        :type event_logging: bool
        :param file_logging: If true, system logs recorded data to file. Else not.
        :type file_logging: bool
        """
        if event_logging:
            self.logger.start_logging()
        else:
            self.logger.stop_logging()

        self.logger.configure_file_logging(file_logging)

    def authenticate(
            self,
            id: str,
            continuous_auth: bool = False,
            timeout_s: float = 10,
            threshold: Optional[float] = None,
            template_mode: Optional[TemplateMode] = None,
            similarity_mode: Optional[SimilarityMode] = None) -> bool:
        """Authenticate a user using their brainwaves. If continuous authentication is enabled, the user is instantly authenticated if the system has already authenticated the user in the past.
        If the user is not authenticated, the system will perform a new authentication.

        :param id: Id of the user to be authenticated.
        :type id: str
        :param continuous_auth: If set to true, user will instantly be authentication if the system has already authenticated the user in the past. Else, the system will perform a new authentication. defaults to False
        :type continuous_auth: bool, optional
        :param timeout_s: Maximum time the authentication process is allowed to take. defaults to 10
        :type timeout_s: float, optional
        :param threshold: Minimum similarity threshold between two samples to be considered equal. If no threshold is supplied, the default threshold is used. defaults to None
        :type threshold: Optional[float], optional
        :param template_mode: Template creation mode. If no mode is supplied, the default mode is used. defaults to None
        :type template_mode: Optional[TemplateMode], optional
        :param similarity_mode: Similarity mode for multiple samples. If no mode is supplied, the default mode is used. defaults to None
        :type similarity_mode: Optional[SimilarityMode], optional
        :return: True if authentication was successful, else false
        :rtype: bool
        """
        # Log start of authentication
        self.logger.log_info("Starting Authentication")
        self.logger.log_database(self.database)

        # Check, that device is connected. Else we can not authenticate
        if not self.device.is_connected():
            self.logger.log_fail(
                "Authentication failed due to no device being present")
            return False

        # Check if id is registered in database
        if id not in self.database.get_all_idents():
            self.logger.log_fail("Authentication failed due to unknown id")
            return False

        # Check for custom values. If no supplied use defaults
        if not threshold:
            threshold = self.default_threshold

        if not template_mode:
            template_mode = self.template_mode

        if not similarity_mode:
            similarity_mode = self.similarity_mode

        # Log new parameters
        self.logger.log_info(
            f"Performing authentication with parameters: id={id}, continuous_auth={continuous_auth}, timeout_s={timeout_s}, threshold={threshold}, template_mode={template_mode}, similarity_mode={similarity_mode}")

        # If we continuously authenticate, check that device was constantly on
        # the user's head
        if continuous_auth and self.last_auth > self.device.removal_time_stamp:
            # Extra check that device is still on head. This is necessary as it can stop
            # Without updating the removal_time_stamp properly.
            if not self.device.is_worn():
                self.device.removal_time_stamp = time()
                self.logger.log_fail(
                    "Authentication failed! Device is not on head or not connected."
                )
                return False

            # Check that the last id authenticated is equal to the current one.
            if id == self.last_id:
                self.logger.log_info(
                    "Authenticated user using continuous authentication mode")
                return True

        # Get events for recording duration
        try:
            events = self.__perform_task_rec(timeout_s)
        except AuthException as e:
            self.last_auth = 0
            self.logger.log_fail(f"Authentication failed \"{e.args}\".")
            return False

        # Apply preprocessing
        self.preprocessing_pipeline.apply(events)
        self.logger.log_info(f"Applying {self.preprocessing_pipeline}")

        # Create templates
        templates = self.__create_templates(events, template_mode)

        # Calculate similarity
        sims = self.__calculate_similarity(templates, similarity_mode, id)

        # We expect exactly one similarity value as we are doing authentication
        if len(sims) != 1:
            self.logger.log_fail(
                "Authentication failed! Found not exactly one similarity in results")
            return False

        # Check if similarity is nan
        # More of a failsafe as this should not happen
        if np.isnan(sims[0][1]):
            self.logger.log_fail(
                f"Authentication failed! Similarity was nan."
            )
            return False

        # Check if similarity is below threshold
        # If so, authentication failed
        if sims[0][1] < threshold:
            self.logger.log_fail(
                f"Authentication failed! Similarity was below threshold {sims[0][1]} < {threshold}")
            return False

        # Authentication successful
        # Update system state for continuous authentication
        self.last_auth = time()
        self.last_id = id

        # Log successful authentication
        self.logger.log_info(
            f"Authentication successful! Similarity was above threshold {sims[0][1]} > {threshold}")

        # Return true
        return True

    def identify(self,
                 timeout_s: float = 10,
                 threshold: Optional[float] = None,
                 template_mode: Optional[TemplateMode] = None,
                 similarity_mode: Optional[SimilarityMode] = None) -> Tuple[bool,
                                                                            Union[str,
                                                                                  None]]:
        """Identify a user using their brainwaves.

        :param timeout_s: Maximum time the identification process is allowed to take. defaults to 10
        :type timeout_s: float, optional
        :param threshold: Minimum similarity threshold between two samples to be considered equal. If no threshold is supplied, the default threshold is used. defaults to None
        :type threshold: Optional[float], optional
        :param template_mode: Template creation mode. If no mode is supplied, the default mode is used. defaults to None
        :type template_mode: Optional[TemplateMode], optional
        :param similarity_mode: Similarity mode for multiple samples. If no mode is supplied, the default mode is used. defaults to None
        :type similarity_mode: Optional[SimilarityMode], optional
        :return: Tuple of bool and str. Bool is true if identification was successful, else false. Str is the id of the identified user, if successful, else None.
        :rtype: Tuple[bool, str]
        """
        # Log start of identification
        self.logger.log_info("Starting Identification")
        self.logger.log_database(self.database)

        # Check, that device is connected. Else we can not Identify
        if not self.device.is_connected():
            self.logger.log_fail(
                "Identification failed due to no device being present")
            return False, None

        # Check for custom values. If no supplied use defaults
        if not threshold:
            threshold = self.default_threshold

        if not template_mode:
            template_mode = self.template_mode

        if not similarity_mode:
            similarity_mode = self.similarity_mode

        # Log new parameters
        self.logger.log_info(
            f"Performing Identification with parameters: timeout_s={timeout_s}, threshold={threshold}, template_mode={template_mode}, similarity_mode={similarity_mode}")

        # Get events for recording duration
        try:
            events = self.__perform_task_rec(timeout_s)
        except AuthException as e:
            self.logger.log_fail(f"Identification failed \"{e.args}\".")
            return False, None

        # Apply preprocessing
        self.preprocessing_pipeline.apply(events)
        self.logger.log_info(f"Applying {self.preprocessing_pipeline}")

        # Create templates
        templates = self.__create_templates(events, template_mode)

        # Calculate similarity
        sims = self.__calculate_similarity(templates, similarity_mode)

        if not len(sims):
            self.logger.log_fail(
                "Identification failed! No similarities where computed")
            return False, ""

        if sims[0][1] < threshold:
            self.logger.log_fail(
                "Identification failed! Highest similarity below threshold. {} < {}")
            return False, ""

        # Enrollment counts as new authentication
        self.logger.log_info(
            f"Identification successful. Identified as {sims[0][0]}")
        return True, sims[0][0]

    def enroll(
            self,
            id: str,
            timeout_s: float = 60,
            enrollment_mode: Optional[TemplateMode] = None) -> bool:
        """Enroll a user using their brainwaves. The user is identified by the id parameter.

        :param id: Id of newly enrolled user. Must be unique.
        :type id: str
        :param timeout_s: Maximum time the enrollment process is allowed to take. defaults to 60
        :type timeout_s: Optional[float], optional
        :param enrollment_mode: Template creation mode. If no mode is supplied, the default mode is used. defaults to None
        :type enrollment_mode: Optional[TemplateMode], optional
        :return: True if enrollment was successful, else False
        :rtype: bool
        """
        # Log start of Enrollment
        self.logger.log_info("Starting Enrollment")
        self.logger.log_info("Database before enrollment")
        self.logger.log_database(self.database)

        # Check, that device is connected. Else we can not enroll.
        if not self.device.is_connected():
            self.logger.log_fail(
                "Enrollment failed due to no device being present")
            return False

        # Check if enrollment_mode is set. Else fallback to default
        if not enrollment_mode:
            enrollment_mode = self.template_mode

        # Log new parameters
        self.logger.log_info(
            f"Performing Enrollment with parameters: id={id}, timeout_s={timeout_s}, enrollment_mode={enrollment_mode}")

        # Get events for recording duration
        try:
            events = self.__perform_task_rec(timeout_s)
        except AuthException as e:
            self.logger.log_fail(f"Enrollment failed \"{e.args}\".")
            return False

        # Apply preprocessing to recorded events
        self.preprocessing_pipeline.apply(events)
        self.logger.log_info(f"Applying {self.preprocessing_pipeline}")

        # Add templates to database
        for t in self.__create_templates(events, enrollment_mode):
            self.database.add_template(id, t)

        self.logger.log_info(
            f"Added new template(s) for id \"{id}\" to database")
        self.logger.log_database(self.database)

        # Enrollment counts as new authentication
        self.last_auth = time()
        self.last_id = id

        # Everything done!
        return True

    def get_database(self) -> TemplateDatabase:
        """Returns used database object.

        :return: Database
        :rtype: TemplateDatabase
        """
        return self.database

    def get_database_as_dict(self) -> dict:
        """Returns content of used database in dictionary form. Useful for state saving.

        :return: Database state as dictionary
        :rtype: dict
        """
        return self.database.internal_data

    def __create_templates(
            self,
            events: List[EventContainer],
            mode: TemplateMode) -> List[NDArray]:
        """Transforms events into templates according to chosen model and mode.

        :param events: List of events. Should be preprocessed before using this function.
        :type events: List[EventContainer]
        :param mode: Mode selection for template creation. Average indicates, that template is generated by averaging all recorded events to yield highest signal-to-noise ratio. Single indicates, that each recorded event is transformed into a single template, with multiple templates being stored for each user
        :type mode: TemplateMode
        :return: Created templates or template
        :rtype: List[NDArray]
        """
        templates = []
        # Depending on the selected mode we not transform our observations
        if mode in [
                TemplateMode.AverageAndSingleTemplates,
                TemplateMode.AverageTemplate]:
            avg = osum(events) / len(events)
            templates.append(self.feature_extraction.extract_features(avg))

        if mode in [
                TemplateMode.SingleTemplates,
                TemplateMode.AverageAndSingleTemplates]:
            for e in events:
                templates.append(self.feature_extraction.extract_features(e))

        return templates

    def __perform_task_rec(self, timeout_s: float) -> List[EventContainer]:
        """Function to record brainwaves while an acquisition task is played out for the user. After the acquisition task is finished, extract all points of interest from the recording according to previously defined parameters, e.g., the time before and after an event to be included.

        :param timeout_s: Length of acquisition task.
        :type timeout_s: float
        :raises AuthException: Raises exceptions if anything goes wrong during recording.
        :return: All events (ERPs) recorded during acquisition task.
        :rtype: List[EventContainer]
        """
        self.logger.log_info("Starting Task")

        eeg_container = EEGContainer(
            self.device.channel_names,
            self.device.sample_rate)
        stimuli_times = []

        start = time()
        self.device.start_stream()
        self.task.start()
        while time() - start < timeout_s and self.task.is_alive():
            # Check, that device was not taken off after start of enrollment.
            if self.device.removal_time_stamp > start or not self.device.is_worn():
                self.device.stop_stream()
                self.task.stop()
                raise AuthException("Device not on head")

            # Check, that task was not aborted by user
            if self.task.aborted:
                if self.task.is_alive():
                    self.task.stop()
                raise AuthException("Task was stopped early")

            # Fetch data from device
            if self.device.has_data():
                eeg_container.add_data(self.device.fetch_data())

        # We are done getting data for given time frame
        self.device.stop_stream()

        # Get timings of task after completing data acquisition
        stop_time = time()
        while self.task.has_data():
            t = self.task.fetch_data()
            if t.timestamp > stop_time or not self.task.is_alive():
                break
            if t.is_target:
                stimuli_times.append(t.timestamp)
        self.task.stop()

        # Fetch all recorded events. Remove events until all events are of same
        # length.
        events = []
        for time_stamp in stimuli_times:
            eeg_container.mark_event(1, time_stamp)

        events = eeg_container.get_events(
            1, self.before_event_time_ms, self.after_event_time_ms)

        # Events can possibly be shorter than needed. Remove events which do not have
        # enough data points.
        while len(events[0]) != len(events[-1]):
            events = events[:-1]

        # Log EEGContainer
        self.logger.log_info(
            "Expected ~" + str(self.device.sample_rate * timeout_s) + " timestamps")
        self.logger.log_info("Recorded " +
                             str(len(eeg_container.timestamps)) +
                             " timestamps")
        self.logger.log_info(
            "Recorded " + str(len(events)) + " events")
        self.logger.log_recording(eeg_container)
        self.logger.log_info("Task finished")

        # Return all events
        return events

    def __calculate_similarity(self,
                               templates: List[NDArray],
                               similarity_mode: SimilarityMode,
                               id: Optional[str] = None) -> List[Tuple[str,
                                                                       float]]:
        """Function to calculate the similarity between one or more database entries and a new recording.

        :param templates: Templates to be compared against stored templates.
        :type templates: List[NDArray]
        :param similarity_mode: Comparison mode, either the average similarity for all stored templates is returned or the highest similarity
        :type similarity_mode: SimilarityMode
        :return: Returns a list containing the similarity for the given id if specified. Else returns the similarity for all ids stored inside the database, useful for identification.
        :rtype: List[Tuple[str, float]]
        """
        global_sims = []

        # Check if an id was specified. If not, we compare against all stored
        # ids
        if not id:
            ids = self.database.get_all_idents()
        else:
            ids = [id]

        # Iterate over all ids and calculate similarity
        for id in ids:
            sims = []

            # Get stored templates for id
            stored_templates = self.database.get_templates(id)

            # Database returns false in tuple, if no templates are stored for
            # id
            if not stored_templates[0]:
                continue

            # We further check for the case, that no templates are stored for
            # id
            if not stored_templates[1]:
                continue

            # Calculate similarity for each template stored
            for st in stored_templates[1]:
                for t in templates:
                    sims.append(self.similarity_metric(st, t))

            # Depending on the similarity mode, we either return the average or
            # the maximum similarity. If only one template is stored,
            # similarity is equal to the only stored template in
            # both cases.
            if similarity_mode == SimilarityMode.AverageSimilarity:
                sim = sum(sims) / len(sims)
            else:
                sim = max(sims)

            # Append similarity to global list
            global_sims.append((id, sim))

        # Sort list by similarity, highest similarity first
        # This is useful for identification
        # In case we only compared against one id, sorting
        # does not change anything
        global_sims.sort(key=lambda x: x[1], reverse=True)

        # Return list of similarities
        return global_sims
