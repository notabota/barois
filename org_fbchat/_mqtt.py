import attr
import random
import paho.mqtt.client
from ._core import log
from . import _util, _exception, _graphql


def generate_session_id():
    """Generate a random session ID between 1 and 9007199254740991."""
    return random.randint(1, 2 ** 53)


@attr.s(slots=True)
class Mqtt(object):
    _state = attr.ib()
    _mqtt = attr.ib()
    _on_message = attr.ib()
    _chat_on = attr.ib()
    _foreground = attr.ib()
    _sequence_id = attr.ib()
    _sync_token = attr.ib(None)

    _HOST = "edge-chat.facebook.com"

    @classmethod
    def connect(cls, state, on_message, chat_on, foreground):
        mqtt = paho.mqtt.client.Client(
            client_id="mqttwsclient",
            clean_session=True,
            protocol=paho.mqtt.client.MQTTv31,
            transport="websockets",
        )
        mqtt.enable_logger()
        # mqtt.max_inflight_messages_set(20)  # The rest will get queued
        # mqtt.max_queued_messages_set(0)  # Unlimited messages can be queued
        # mqtt.message_retry_set(20)  # Retry sending for at least 20 seconds
        # mqtt.reconnect_delay_set(min_delay=1, max_delay=120)
        # TODO: Is region (lla | atn | odn | others?) important?
        mqtt.tls_set()

        self = cls(
            state=state,
            mqtt=mqtt,
            on_message=on_message,
            chat_on=chat_on,
            foreground=foreground,
            sequence_id=cls._fetch_sequence_id(state),
        )

        # Configure callbacks
        mqtt.on_message = self._on_message_handler
        mqtt.on_connect = self._on_connect_handler

        self._configure_connect_options()

        # Attempt to connect
        try:
            rc = mqtt.connect(self._HOST, 443, keepalive=10)
        except (
            # Taken from .loop_forever
            paho.mqtt.client.socket.error,
            OSError,
            paho.mqtt.client.WebsocketConnectionError,
        ) as e:
            print(str(e))
            raise _exception.FBchatException("MQTT connection failed")

        # Raise error if connecting failed
        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            err = paho.mqtt.client.error_string(rc)
            raise _exception.FBchatException("MQTT connection failed: {}".format(err))

        return self

    def _on_message_handler(self, client, userdata, message):
        # Parse payload JSON
        try:
            j = _util.parse_json(message.payload.decode("utf-8"))
        except (_exception.FBchatFacebookError, UnicodeDecodeError):
            log.exception("Failed parsing MQTT data on %s as JSON", message.topic)
            return

        log.debug("MQTT payload: %s, %s", message.topic, j)

        if message.topic == "/t_ms":
            # Update sync_token when received
            # This is received in the first message after we've created a messenger
            # sync queue.
            if "syncToken" in j and "firstDeltaSeqId" in j:
                self._sync_token = j["syncToken"]
                self._sequence_id = j["firstDeltaSeqId"]
                return

            # Update last sequence id when received
            if "lastIssuedSeqId" in j:
                self._sequence_id = j["lastIssuedSeqId"]

            if "errorCode" in j:
                error = j["errorCode"]
                # TODO: 'F\xfa\x84\x8c\x85\xf8\xbc-\x88 FB_PAGES_INSUFFICIENT_PERMISSION\x00'
                if error in ("ERROR_QUEUE_NOT_FOUND", "ERROR_QUEUE_OVERFLOW"):
                    # ERROR_QUEUE_NOT_FOUND means that the queue was deleted, since too
                    # much time passed, or that it was simply missing
                    # ERROR_QUEUE_OVERFLOW means that the sequence id was too small, so
                    # the desired events could not be retrieved
                    log.error(
                        "The MQTT listener was disconnected for too long,"
                        " events may have been lost"
                    )
                    self._sync_token = None
                    self._sequence_id = self._fetch_sequence_id(self._state)
                    self._messenger_queue_publish()
                    # TODO: Signal to the user that they should reload their data!
                    return
                log.error("MQTT error code %s received", error)
                return

        # Call the external callback
        self._on_message(message.topic, j)

    @staticmethod
    def _fetch_sequence_id(state):
        """Fetch sequence ID."""
        params = {
            "limit": 1,
            "tags": ["INBOX"],
            "before": None,
            "includeDeliveryReceipts": False,
            "includeSeqID": True,
        }
        log.debug("Fetching MQTT sequence ID")
        # Same request as in `Client.fetchThreadList`
        (j,) = state._graphql_requests(_graphql.from_doc_id("1349387578499440", params))
        print(j)
        j = {'viewer': {'message_threads': {'sync_sequence_id': '2506', 'nodes': [{'thread_key': {'thread_fbid': None, 'other_user_id': '100025390244911'}, 'name': None, 'last_message': {'nodes': [{'snippet': 'Tf you talking about heyo', 'message_sender': {'messaging_actor': {'id': '100082509364555'}}, 'timestamp_precise': '1655998373275', 'commerce_message_type': None, 'extensible_attachment': None, 'sticker': None, 'blob_attachments': []}]}, 'unread_count': 70, 'messages_count': 72, 'image': None, 'updated_time_precise': '1655998373275', 'mute_until': None, 'is_pin_protected': False, 'is_viewer_subscribed': True, 'thread_queue_enabled': False, 'folder': 'INBOX', 'has_viewer_archived': False, 'is_page_follow_up': False, 'cannot_reply_reason': None, 'ephemeral_ttl_mode': 0, 'customization_info': None, 'thread_admins': [], 'approval_mode': None, 'joinable_mode': {'mode': '0', 'link': ''}, 'thread_queue_metadata': None, 'event_reminders': {'nodes': []}, 'montage_thread': {'id': 'bWVzc2FnZV90aHJlYWQ6MzA4MzgyMTkwMDE4MTIw'}, 'last_read_receipt': {'nodes': [{'timestamp_precise': '1655269222006'}]}, 'related_page_thread': None, 'rtc_call_data': {'call_state': 'NO_ONGOING_CALL', 'server_info_data': '', 'initiator': None}, 'associated_object': None, 'privacy_mode': 1, 'reactions_mute_mode': 'REACTIONS_NOT_MUTED', 'mentions_mute_mode': 'MENTIONS_NOT_MUTED', 'customization_enabled': True, 'thread_type': 'ONE_TO_ONE', 'participant_add_mode_as_string': None, 'is_canonical_neo_user': False, 'participants_event_status': [], 'page_comm_item': None, 'all_participants': {'nodes': [{'messaging_actor': {'id': '100025390244911', '__typename': 'User', 'name': 'Nguyễn Nguyên Vũ', 'gender': 'NEUTER', 'url': 'https://www.facebook.com/nnv2205owo', 'big_image_src': {'uri': 'https://scontent.fsgn2-4.fna.fbcdn.net/v/t39.30808-1/262855038_1032913320898333_7233575726289334811_n.jpg?stp=c0.0.50.50a_cp0_dst-jpg_p50x50&_nc_cat=109&ccb=1-7&_nc_sid=7206a8&_nc_ohc=fRSdUW2RWM4AX-1Lfss&_nc_ht=scontent.fsgn2-4.fna&oh=00_AT9syrMeXZ2z6LvCia2nJgb3wT-5tjz45yH-g4-PfIWMgA&oe=62B967C2'}, 'short_name': 'Nguyên Vũ', 'username': 'nnv2205owo', 'is_viewer_friend': True, 'is_messenger_user': True, 'is_verified': False, 'is_message_blocked_by_viewer': False, 'is_viewer_coworker': False, 'is_employee': None}}, {'messaging_actor': {'id': '100082509364555', '__typename': 'User', 'name': 'Ba Rois', 'gender': 'MALE', 'url': 'https://www.facebook.com/profile.php?id=100082509364555', 'big_image_src': {'uri': 'https://scontent.fsgn2-4.fna.fbcdn.net/v/t39.30808-1/288122467_101566829270296_1820462479484112718_n.jpg?stp=cp0_dst-jpg_p50x50&_nc_cat=109&ccb=1-7&_nc_sid=7206a8&_nc_ohc=hqGOWlUIlGsAX_D2mFc&_nc_ht=scontent.fsgn2-4.fna&oh=00_AT99Zf9-TQ_nfipTLB9AzRC0IEVgOvolI-kiyLV1_z8f5g&oe=62BAD0E5'}, 'short_name': 'Ba', 'username': '', 'is_viewer_friend': False, 'is_messenger_user': False, 'is_verified': False, 'is_message_blocked_by_viewer': False, 'is_viewer_coworker': False, 'is_employee': None}}]}, 'read_receipts': {'nodes': [{'watermark': '1655989863853', 'action': '1655989864615', 'actor': {'id': '100025390244911'}}, {'watermark': '1655269222006', 'action': '1655269222006', 'actor': {'id': '100082509364555'}}]}}]}}}
        sequence_id = j["viewer"]["message_threads"]["sync_sequence_id"]
        if not sequence_id:
            raise _exception.FBchatNotLoggedIn("Failed fetching sequence id")
        return int(sequence_id)

    def _on_connect_handler(self, client, userdata, flags, rc):
        if rc == 21:
            raise _exception.FBchatException(
                "Failed connecting. Maybe your cookies are wrong?"
            )
        if rc != 0:
            return  # Don't try to send publish if the connection failed

        self._messenger_queue_publish()

    def _messenger_queue_publish(self):
        # configure receiving messages.
        payload = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self._state.user_id,
        }

        # If we don't have a sync_token, create a new messenger queue
        # This is done so that across reconnects, if we've received a sync token, we
        # SHOULD receive a piece of data in /t_ms exactly once!
        if self._sync_token is None:
            topic = "/messenger_sync_create_queue"
            payload["initial_titan_sequence_id"] = str(self._sequence_id)
            payload["device_params"] = None
        else:
            topic = "/messenger_sync_get_diffs"
            payload["last_seq_id"] = str(self._sequence_id)
            payload["sync_token"] = self._sync_token

        self._mqtt.publish(topic, _util.json_minimal(payload), qos=1)

    def _configure_connect_options(self):
        # Generate a new session ID on each reconnect
        session_id = generate_session_id()

        topics = [
            # Things that happen in chats (e.g. messages)
            "/t_ms",
            # Group typing notifications
            "/thread_typing",
            # Private chat typing notifications
            "/orca_typing_notifications",
            # Active notifications
            "/orca_presence",
            # Other notifications not related to chats (e.g. friend requests)
            "/legacy_web",
            # Facebook's continuous error reporting/logging?
            "/br_sr",
            # Response to /br_sr
            "/sr_res",
            # Data about user-to-user calls
            # TODO: Investigate the response from this! (A bunch of binary data)
            # "/t_rtc",
            # TODO: Find out what this does!
            # TODO: Investigate the response from this! (A bunch of binary data)
            # "/t_p",
            # TODO: Find out what this does!
            "/webrtc",
            # TODO: Find out what this does!
            "/onevc",
            # TODO: Find out what this does!
            "/notify_disconnect",
            # Old, no longer active topics
            # These are here just in case something interesting pops up
            "/inbox",
            "/mercury",
            "/messaging_events",
            "/orca_message_notifications",
            "/pp",
            "/webrtc_response",
        ]

        username = {
            # The user ID
            "u": self._state.user_id,
            # Session ID
            "s": session_id,
            # Active status setting
            "chat_on": self._chat_on,
            # foreground_state - Whether the window is focused
            "fg": self._foreground,
            # Can be any random ID
            "d": self._state._client_id,
            # Application ID, taken from facebook.com
            "aid": 219994525426954,
            # MQTT extension by FB, allows making a SUBSCRIBE while CONNECTing
            "st": topics,
            # MQTT extension by FB, allows making a PUBLISH while CONNECTing
            # Using this is more efficient, but the same can be acheived with:
            #     def on_connect(*args):
            #         mqtt.publish(topic, payload, qos=1)
            #     mqtt.on_connect = on_connect
            # TODO: For some reason this doesn't work!
            "pm": [
                # {
                #     "topic": topic,
                #     "payload": payload,
                #     "qos": 1,
                #     "messageId": 65536,
                # }
            ],
            # Unknown parameters
            "cp": 3,
            "ecp": 10,
            "ct": "websocket",
            "mqtt_sid": "",
            "dc": "",
            "no_auto_fg": True,
            "gas": None,
            "pack": [],
        }

        # TODO: Make this thread safe
        self._mqtt.username_pw_set(_util.json_minimal(username))

        headers = {
            # TODO: Make this access thread safe
            "Cookie": _util.get_cookie_header(
                self._state._session, "https://edge-chat.facebook.com/chat"
            ),
            "User-Agent": self._state._session.headers["User-Agent"],
            "Origin": "https://www.facebook.com",
            "Host": self._HOST,
        }

        self._mqtt.ws_set_options(
            path="/chat?sid={}".format(session_id), headers=headers
        )

    def loop_once(self, on_error=None):
        """Run the listening loop once.

        Returns whether to keep listening or not.
        """
        rc = self._mqtt.loop(timeout=1.0)

        # If disconnect() has been called
        if self._mqtt._state == paho.mqtt.client.mqtt_cs_disconnecting:
            return False  # Stop listening

        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            # If known/expected error
            if rc == paho.mqtt.client.MQTT_ERR_CONN_LOST:
                log.warning("Connection lost, retrying")
            elif rc == paho.mqtt.client.MQTT_ERR_NOMEM:
                # This error is wrongly classified
                # See https://github.com/eclipse/paho.mqtt.python/issues/340
                log.warning("Connection error, retrying")
            elif rc == paho.mqtt.client.MQTT_ERR_CONN_REFUSED:
                raise _exception.FBchatNotLoggedIn("MQTT connection refused")
            else:
                err = paho.mqtt.client.error_string(rc)
                log.error("MQTT Error: %s", err)
                # For backwards compatibility
                if on_error:
                    on_error(_exception.FBchatException("MQTT Error {}".format(err)))

            # Wait before reconnecting
            self._mqtt._reconnect_wait()

            # Try reconnecting
            self._configure_connect_options()
            try:
                self._mqtt.reconnect()
            except (
                # Taken from .loop_forever
                paho.mqtt.client.socket.error,
                OSError,
                paho.mqtt.client.WebsocketConnectionError,
            ) as e:
                log.debug("MQTT reconnection failed: %s", e)

        return True  # Keep listening

    def disconnect(self):
        self._mqtt.disconnect()

    def set_foreground(self, value):
        payload = _util.json_minimal({"foreground": value})
        info = self._mqtt.publish("/foreground_state", payload=payload, qos=1)
        self._foreground = value
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()

    def set_chat_on(self, value):
        # TODO: Is this the right request to make?
        data = {"make_user_available_when_in_foreground": value}
        payload = _util.json_minimal(data)
        info = self._mqtt.publish("/set_client_settings", payload=payload, qos=1)
        self._chat_on = value
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()

    # def send_additional_contacts(self, additional_contacts):
    #     payload = _util.json_minimal({"additional_contacts": additional_contacts})
    #     info = self._mqtt.publish("/send_additional_contacts", payload=payload, qos=1)
    #
    # def browser_close(self):
    #     info = self._mqtt.publish("/browser_close", payload=b"{}", qos=1)
