import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from click.testing import CliRunner

from srtgo.ktx import (Korail, KorailError, NeedToLoginError,
                      ReservationOutcomeUnknown, ReserveOption, ServiceUnavailableError)
from srtgo import srtgo as ui


def train_data(number='001', kind='00'):
    return {'h_trn_no': number, 'h_trn_clsf_cd': kind, 'h_trn_clsf_nm': 'KTX',
            'h_trn_gp_cd': '100', 'h_dpt_dt': '20261122', 'h_dpt_tm': '120000',
            'h_dpt_rs_stn_cd': '0020', 'h_dpt_rs_stn_nm': '부산',
            'h_arv_rs_stn_cd': '0001', 'h_arv_rs_stn_nm': '서울',
            'h_arv_dt': '20261122', 'h_arv_tm': '145000', 'h_run_dt': '20261122',
            'h_gen_rsv_cd': '11', 'h_spe_rsv_cd': '13', 'h_wait_rsv_flg': '0'}


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.rail = Korail('', '', auto_login=False)
        self.rail._session = Mock()

    def response(self, payload):
        self.rail._session.get.return_value.text = json.dumps(payload)

    def test_unified_search_includes_srt_and_carries_passenger_count(self):
        self.response({'strResult': 'SUCC', 'trn_infos': {'trn_info': [train_data(), train_data('302', '17')]}})
        trains = self.rail.search_train('부산', '서울', '20261122', '000000', include_no_seats=True)
        self.assertEqual(len(trains), 2)
        params = self.rail._session.get.call_args.kwargs['params']
        self.assertEqual(params['srtCheckYn'], 'Y')
        self.assertEqual(params['txtGoStart'], '부산')
        self.assertEqual(params['txtGoEnd'], '서울')
        self.assertEqual(params['txtPsgFlg_1'], 1)

    def test_srt_inclusion_can_be_disabled(self):
        self.response({'strResult': 'SUCC', 'trn_infos': {'trn_info': [train_data()]}})
        self.rail.search_train('부산', '서울', include_no_seats=True, include_srt=False)
        self.assertEqual(self.rail._session.get.call_args.kwargs['params']['srtCheckYn'], 'N')

    def test_server_rejection_is_terminal(self):
        self.response({'strResult': 'FAIL', 'h_msg_cd': 'MACRO ERROR', 'h_msg_txt': 'update'})
        with self.assertRaises(ServiceUnavailableError):
            self.rail.search_train('부산', '서울')
        self.assertEqual(self.rail._session.get.call_count, 1)

    def test_unknown_response_is_not_success(self):
        with self.assertRaises(KorailError):
            self.rail._result_check({})

    def test_failed_login_is_not_saved(self):
        with patch.object(ui.inquirer, 'prompt', return_value={'id': 'test', 'pass': 'dummy'}), \
             patch.object(ui.keyring, 'get_password', return_value=None), \
             patch.object(ui.keyring, 'set_password') as save, \
             patch.object(ui, 'Korail', return_value=SimpleNamespace(is_login=False)):
            self.assertFalse(ui.set_login())
            save.assert_not_called()

    def test_cancelled_login_does_not_construct_client(self):
        with patch.object(ui.keyring, 'get_password', return_value=None), \
             patch.object(ui, 'set_login', return_value=False), \
             patch.object(ui, 'Korail') as client:
            with self.assertRaises(NeedToLoginError):
                ui.login()
            client.assert_not_called()

    def test_reserve_requires_login(self):
        with self.assertRaises(NeedToLoginError):
            self.rail.reserve(Mock())
        self.rail._session.get.assert_not_called()

    def test_ambiguous_reservation_is_not_retried(self):
        from srtgo.ktx import Train
        self.rail.logined = True
        self.rail._session.get.side_effect = TimeoutError()
        with self.assertRaises(ReservationOutcomeUnknown):
            self.rail.reserve(Train(train_data()), option=ReserveOption.GENERAL_ONLY)
        self.assertEqual(self.rail._session.get.call_count, 1)

    def test_srt_reservation_uses_returned_train_codes(self):
        from srtgo.ktx import Train
        self.rail.logined = True
        self.response({'strResult': 'SUCC', 'h_pnr_no': 'test-reservation'})
        expected = object()
        self.rail.reservations = Mock(return_value=expected)
        self.assertIs(self.rail.reserve(Train(train_data('302', '17'))), expected)
        params = self.rail._session.get.call_args.kwargs['params']
        self.assertEqual(params['txtTrnClsfCd1'], '17')
        self.assertEqual(params['txtTrnNo1'], '302')
        self.rail.reservations.assert_called_once_with('test-reservation')

    def test_selection_follows_train_identity_when_results_reorder(self):
        from srtgo.ktx import Train
        first, second = Train(train_data('001')), Train(train_data('302', '17'))
        identity = ui._train_identity(first, 'KTX')
        reordered = [second, first]
        self.assertEqual([t.train_no for t in reordered if ui._train_identity(t, 'KTX') == identity], ['001'])

    def exercise_reservation_ui(self, search_result, notification_failure=False):
        from contextlib import ExitStack
        from srtgo.ktx import Train
        first, second = Train(train_data('001')), Train(train_data('302', '17'))
        rail = Mock()
        rail.search_train.side_effect = [[first, second], search_result(first, second)]
        rail.reserve.return_value = SimpleNamespace(is_waiting=False)
        info = {'departure': '부산', 'arrival': '서울', 'date': '20261122',
                'time': '000000', 'adult': 1}

        async def notify(message):
            if notification_failure:
                raise RuntimeError('notification failed')

        with ExitStack() as stack:
            stack.enter_context(patch.object(ui, 'login', return_value=rail))
            stack.enter_context(patch.object(ui, 'get_options', return_value=[]))
            stack.enter_context(patch.object(ui, 'get_station', return_value=(['부산', '서울'], ['부산', '서울'])))
            stack.enter_context(patch.object(ui.keyring, 'get_password', return_value=None))
            stack.enter_context(patch.object(ui.keyring, 'set_password'))
            stack.enter_context(patch.object(ui.inquirer, 'prompt', side_effect=[
                info, {'trains': [0]}, {'type': ReserveOption.GENERAL_ONLY, 'pay': False}]))
            stack.enter_context(patch.object(ui, 'get_telegram', return_value=notify))
            handler = stack.enter_context(patch.object(ui, '_handle_error', side_effect=AssertionError('must stop')))
            ui.reserve()
            handler.assert_not_called()
        return rail, first

    def test_full_ui_reserves_selected_train_after_reordering(self):
        rail, selected = self.exercise_reservation_ui(lambda first, second: [second, first])
        self.assertIs(rail.reserve.call_args.args[0], selected)
        rail.reserve.assert_called_once()

    def test_notification_failure_does_not_repeat_reservation(self):
        rail, _ = self.exercise_reservation_ui(lambda first, second: [first, second], True)
        rail.reserve.assert_called_once()
        self.assertEqual(rail.search_train.call_count, 2)

    def test_unified_station_list_contains_both_terminals(self):
        self.assertIn('서울', ui.STATIONS['KTX'])
        self.assertIn('수서', ui.STATIONS['KTX'])
        self.assertIn('수서', ui.DEFAULT_STATIONS['KTX'])

    def test_cli_exits_without_old_operator_prompt(self):
        with patch.object(ui.inquirer, 'list_input', return_value=-1) as prompt:
            result = CliRunner().invoke(ui.srtgo)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('코레일+', result.output)
        self.assertEqual(prompt.call_count, 1)


if __name__ == '__main__':
    unittest.main()
