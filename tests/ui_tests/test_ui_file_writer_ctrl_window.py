import json
import pytest
from PySide2.QtGui import QStandardItemModel
from mock import Mock
from nexus_constructor.file_writer_ctrl_window import FileWriterCtrl, File, FileWriter
from nexus_constructor.validators import BrokerAndTopicValidator


def test_UI_GIVEN_nothing_WHEN_creating_filewriter_control_window_THEN_broker_field_defaults_are_set_correctly(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)

    assert not window.command_broker_edit.text()
    assert window.command_broker_led.is_off()
    assert not window.command_broker_change_timer.isActive()

    assert not window.status_broker_edit.text()
    assert window.status_broker_led.is_off()
    assert not window.status_broker_change_timer.isActive()


def test_UI_GIVEN_nothing_WHEN_creating_filewriter_control_window_THEN_broker_validators_are_set_correctly(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)

    assert isinstance(window.status_broker_edit.validator(), BrokerAndTopicValidator)
    assert isinstance(window.command_broker_edit.validator(), BrokerAndTopicValidator)
    assert (
        window.command_broker_edit.validator() != window.status_broker_edit.validator()
    )  # make sure they are different objects so that both edits are validated independently from each other.


@pytest.mark.parametrize(
    "test_input", [FileWriter("test", 0), File("test", 0, "123", "321")]
)
def test_UI_GIVEN_time_string_WHEN_setting_time_THEN_last_time_is_stored(
    test_input, qtbot
):
    model = QStandardItemModel()
    qtbot.addWidget(model)
    current_time = "12345678"
    new_time = "23456789"
    FileWriterCtrl._set_time(model, test_input, current_time, new_time)
    assert test_input.last_time == current_time


def test_UI_GIVEN_no_files_WHEN_stop_file_writing_is_clicked_THEN_button_is_disabled(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.files_list.selectedIndexes = lambda: []

    window.file_list_clicked()

    assert not window.stop_file_writing_button.isEnabled()


def test_UI_GIVEN_files_WHEN_stop_file_writing_is_clicked_THEN_button_is_enabled(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.files_list.selectedIndexes = lambda: [
        1,
        2,
        3,
    ]  # Can be any list so doesn't matter what's in here

    window.file_list_clicked()

    assert window.stop_file_writing_button.isEnabled()


def test_UI_GIVEN_valid_command_WHEN_sending_command_THEN_command_producer_sends_command(
    qtbot, instrument
):

    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_producer = Mock()

    broker = "broker1:9092/topic1"
    service_id = "12345678"

    window.command_widget.broker_line_edit.setText(broker)
    window.command_widget.start_time_enabled.setChecked(False)
    window.command_widget.stop_time_enabled.setChecked(False)
    window.command_widget.service_id_lineedit.setText(service_id)

    window.send_command()

    window.command_producer.send_command.assert_called_once()

    sent_msg = window.command_producer.send_command.call_args_list[0][0][0]

    res = json.loads(sent_msg)

    assert res["cmd"] == "FileWriter_new"
    assert res["nexus_structure"]
    assert res["nexus_structure"]["children"]
    assert res["broker"] == broker
    assert res["service_id"] == service_id
    assert not window.command_widget.ok_button.isEnabled()


def test_UI_GIVEN_no_status_consumer_and_no_command_producer_WHEN_checking_status_connection_THEN_both_leds_are_turned_off(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.status_consumer = None
    window.command_producer = None

    window._check_connection_status()

    assert window.status_broker_led.is_off()
    assert window.command_broker_led.is_off()


def test_UI_GIVEN_status_consumer_but_no_command_producer_WHEN_checking_status_connection_THEN_status_led_is_turned_on(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_producer = None
    window.status_consumer = Mock()
    window.status_consumer.connected = True
    window.status_consumer.files = []
    window.status_consumer.file_writers = []

    window._check_connection_status()
    assert window.status_broker_led.is_on()


def test_UI_GIVEN_command_producer_WHEN_checking_connection_status_THEN_command_led_is_turned_on(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_producer = Mock()
    window.status_consumer = None
    window.command_producer.connected = True

    window._check_connection_status()
    assert window.command_broker_led.is_on()


class DummyInterface:
    def __init__(self, address, topic):
        self.address = address
        self.topic = topic


@pytest.mark.skip(reason="qtbot interferes with other tests")
def test_UI_GIVEN_invalid_broker_WHEN_status_broker_timer_callback_is_called_THEN_nothing_happens(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.status_consumer = None
    window.status_broker_edit.setText("invalid")

    window.status_broker_timer_changed(DummyInterface)
    assert window.status_consumer is None


@pytest.mark.skip(reason="qtbot interferes with other tests")
def test_UI_GIVEN_invalid_broker_WHEN_command_broker_timer_callback_is_called_THEN_nothing_happens(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_producer = None
    window.command_broker_edit.setText("invalid")

    window.command_broker_timer_changed(DummyInterface)
    assert window.command_producer is None


@pytest.mark.skip(reason="qtbot interferes with other tests")
def test_UI_GIVEN_valid_broker_WHEN_command_broker_timer_callback_is_called_THEN_producer_is_created(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_broker_change_timer.stop()
    window.status_broker_change_timer.stop()

    window.command_producer = 1  # anything that's not None
    window.command_broker_edit.setText("valid:9092/topic1")

    window.command_broker_timer_changed(DummyInterface)
    assert isinstance(window.command_producer, DummyInterface)


@pytest.mark.skip(reason="qtbot interferes with other tests")
def test_UI_GIVEN_valid_broker_WHEN_status_broker_timer_callback_is_called_THEN_consumer_is_created(
    qtbot, instrument
):
    window = FileWriterCtrl(instrument)
    qtbot.addWidget(window)
    window.command_broker_change_timer.stop()
    window.status_broker_change_timer.stop()

    window.status_consumer = 1  # anything that's not None
    window.status_broker_edit.setText("valid:9092/topic1")

    window.status_broker_timer_changed(DummyInterface)
    assert isinstance(window.status_consumer, DummyInterface)
