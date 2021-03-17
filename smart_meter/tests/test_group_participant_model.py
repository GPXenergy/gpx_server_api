from django.test import TestCase, tag

from smart_meter.models import GroupParticipant
from smart_meter.tests.mixin import MeterTestMixin


@tag('model')
class TestGroupParticipantModel(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.some_group = cls.create_group_meter()

    def setUp(self):
        self.meter = self.create_smart_meter(self.user)

    @tag('model')
    def test_group_participant_save_success(self):
        # given
        participant = GroupParticipant(meter=self.meter, group=self.some_group, )
        # when
        participant.save()
        # then
        # Should be active
        self.assertTrue(participant.active)
        # Should have copied over the initial meter values
        self.assertEqual(self.meter.name, participant.display_name)
        self.assertEqual(self.meter.power_import, participant.power_import_joined)
        self.assertEqual(self.meter.power_export, participant.power_export_joined)
        self.assertEqual(self.meter.total_gas, participant.gas_joined)

    @tag('model')
    def test_group_participant_total_properties_active_success(self):
        # given
        participant = self.create_group_participation(self.meter, self.some_group)
        self.meter.total_power_import_1 += 1
        self.meter.total_power_import_2 += 1
        self.meter.total_power_export_1 += 1
        self.meter.total_power_export_2 += 1
        self.meter.total_gas += 1
        self.meter.save()
        # when
        participant.refresh_from_db()
        # then
        self.assertEqual(2, participant.total_import)
        self.assertEqual(2, participant.total_export)
        self.assertEqual(1, participant.total_gas)

    @tag('model')
    def test_group_participant_total_properties_inactive_success(self):
        # given
        participant = self.create_group_participation(self.meter, self.some_group)
        self.meter.total_power_import_1 += 1
        self.meter.total_power_import_2 += 1
        self.meter.total_power_export_1 += 1
        self.meter.total_power_export_2 += 1
        self.meter.total_gas += 1
        self.meter.save()
        # when
        participant.refresh_from_db()
        participant.leave()
        participant.save()
        # then
        participant.refresh_from_db()
        self.assertEqual(2, participant.total_import)
        self.assertEqual(2, participant.total_export)
        self.assertEqual(1, participant.total_gas)

    @tag('model')
    def test_group_participant_actual_properties_active_success(self):
        # given
        participant = self.create_group_participation(self.meter, self.some_group)
        self.meter.actual_power_import = 2
        self.meter.actual_power_export = 0
        self.meter.actual_gas = 3
        self.meter.actual_solar = 4
        self.meter.save()
        # when
        participant.refresh_from_db()
        # then
        # actual power = export - import
        self.assertEqual(-2, participant.actual_power)
        self.assertEqual(3, participant.actual_gas)
        self.assertEqual(4, participant.actual_solar)

    @tag('model')
    def test_group_participant_actual_properties_inactive_success(self):
        # given
        participant = self.create_group_participation(self.meter, self.some_group)
        self.meter.actual_power_import = 2
        self.meter.actual_power_export = 0
        self.meter.actual_gas = 3
        self.meter.actual_solar = 4
        self.meter.save()
        # when
        participant.refresh_from_db()
        participant.leave()
        participant.save()
        # then
        self.assertEqual(0, participant.actual_power)
        self.assertEqual(0, participant.actual_gas)
        self.assertEqual(0, participant.actual_solar)

    @tag('model')
    def test_group_participant_leave_success(self):
        # given
        participant = self.create_group_participation(self.meter, self.some_group)
        # when
        participant.leave()
        participant.save()
        # then
        self.assertFalse(participant.active)
        self.assertIsNotNone(participant.left_on)

    @tag('manager')
    def test_group_participant_manager_active_success(self):
        # given
        participant1 = self.some_group.participants.first()  # 1st participant already created in setup
        participant2 = self.create_group_participation(self.meter, self.some_group)
        participant3 = self.create_group_participation(self.meter, self.some_group)
        inactive_participant3 = self.create_group_participation(self.meter, self.some_group)
        inactive_participant3.leave()
        inactive_participant3.save()
        # when
        participants = GroupParticipant.objects.active()
        # then
        self.assertEqual(3, participants.count())
        for p in participants:
            self.assertIn(p.pk, [participant1.pk, participant2.pk, participant3.pk])
