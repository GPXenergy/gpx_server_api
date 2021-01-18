from django.test import TestCase, tag
from django.utils import timezone

from smart_meter.models import GroupMeter, SmartMeter
from smart_meter.tests.mixin import MeterTestMixin


@tag('model')
class TestGroupMeterModel(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        # 2 meters managed by user, 1 where user is participant, 1 where user is a past participant and 1 where the
        # user has no relation with the meter
        # 2 of the 5 meters are public
        cls.create_group_meter(cls.user, public=True)
        cls.create_group_meter(cls.user, public=False)
        grp = cls.create_group_meter(public=False)
        cls.create_group_participation(cls.create_smart_meter(cls.user), grp)
        grp2 = cls.create_group_meter(public=False)
        participant = cls.create_group_participation(cls.create_smart_meter(cls.user), grp2)
        participant.leave()
        participant.save()
        cls.create_group_meter(public=True)

    @tag('model')
    def test_group_meter_new_invitation_key_success(self):
        # given
        group = self.create_group_meter(self.create_user())
        current_invitation_key = group.invitation_key
        # when
        group.new_invitation_key()
        # then
        self.assertNotEqual(current_invitation_key, group.invitation_key)

    @tag('model')
    def test_group_meter_new_public_key_success(self):
        # given
        group = self.create_group_meter(self.create_user())
        current_public_key = group.public_key
        # when
        group.new_public_key()
        # then
        self.assertNotEqual(current_public_key, group.public_key)

    @tag('model')
    def test_group_meter_active_participants_success(self):
        # given
        # group with 3 active participants and 3 participants that left
        group = self.create_group_meter(self.create_user())
        for i in range(2):  # initial member + 2
            self.create_group_participation(self.create_smart_meter(self.user), group)
        for i in range(3):  # 3 inactive members
            participant = self.create_group_participation(self.create_smart_meter(self.user), group)
            participant.leave()
            participant.save()
        # when
        active_participants = group.active_participants
        # then
        self.assertEqual(3, active_participants.count())
        for p in active_participants:
            self.assertTrue(p.active)

    @tag('manager')
    def test_group_meter_managed_by_success(self):
        # given
        # when
        groups = GroupMeter.objects.managed_by(self.user.id)
        # then
        self.assertEqual(2, groups.count())
        for g in groups:
            self.assertEqual(self.user.id, g.manager_id)

    @tag('manager')
    def test_group_meter_public_success(self):
        # given
        # when
        groups = GroupMeter.objects.public()
        # then
        self.assertEqual(2, groups.count())
        for g in groups:
            self.assertTrue(g.public)

    @tag('manager')
    def test_group_meter_by_user_success(self):
        # given
        # when
        groups = GroupMeter.objects.by_user(self.user.id)
        # then
        self.assertEqual(3, groups.count())
        for g in groups:
            self.assertTrue(g.participants.active().filter(meter__user_id=self.user.id).exists())

    @tag('manager')
    def test_group_meter_live_groups_success(self):
        # given
        long_time_ago = timezone.now() - timezone.timedelta(seconds=20)
        group_all_active = self.create_group_meter()
        self.create_group_participation(self.create_smart_meter(), group_all_active)
        self.create_group_participation(self.create_smart_meter(), group_all_active)
        group_one_active = self.create_group_meter()
        goa_1 = self.create_group_participation(self.create_smart_meter(), group_one_active)
        goa_2 = self.create_group_participation(self.create_smart_meter(), group_one_active)
        SmartMeter.objects.filter(pk__in=[goa_1.meter_id, goa_2.meter_id]).update(last_update=long_time_ago)
        group_inactive = self.create_group_meter()
        self.create_group_participation(self.create_smart_meter(), group_inactive)
        self.create_group_participation(self.create_smart_meter(), group_inactive)
        SmartMeter.objects.filter(groups=group_inactive).update(last_update=long_time_ago)
        group_ids = [group_all_active.pk, group_one_active.pk, group_inactive.pk]
        # when
        groups = GroupMeter.objects.live_groups(group_ids)
        # then
        self.assertEqual(2, groups.count())
        self.assertTrue(groups.filter(id=group_all_active.pk).exists())
        self.assertTrue(groups.filter(id=group_one_active.pk).exists())
        self.assertFalse(groups.filter(id=group_inactive.pk).exists())

    @tag('manager')
    def test_group_meter_create_success(self):
        # given
        meter = self.create_smart_meter(self.user)
        group_data = {
            'name': 'My groupie!',
            'public': True,
            'meter': meter
        }
        # when
        group = GroupMeter.objects.create(manager=self.user, **group_data)
        # then
        self.assertIsNotNone(group)
        self.assertEqual(group.manager_id, self.user.id)
        self.assertEqual(1, group.participants.count())
        participant = group.participants.first()
        self.assertEqual(meter.id, participant.meter_id)
