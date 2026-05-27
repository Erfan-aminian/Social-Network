from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .captcha import (
    LOGIN_CAPTCHA_SESSION_KEY,
    QUESTION_TYPE_MIN,
    QUESTION_TYPE_SUM,
    QUESTION_TYPES,
    build_login_captcha,
    get_question_text,
)


class LoginCaptchaTests(TestCase):
    def setUp(self):
        self.login_url = reverse('account:user_login')
        self.home_url = reverse('home:home')
        self.user_password = 'complex-pass-123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.user_password
        )

    def _get_captcha_payload(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        captcha_payload = self.client.session.get(LOGIN_CAPTCHA_SESSION_KEY)
        self.assertIsNotNone(captcha_payload)
        return captcha_payload, response

    def _post_login(self, captcha_payload, **overrides):
        payload = {
            'username': self.user.email,
            'password': self.user_password,
            'captcha_answer': captcha_payload['answer'],
            'captcha_token': captcha_payload['token'],
        }
        payload.update(overrides)
        return self.client.post(self.login_url, payload)

    def test_login_page_creates_captcha_payload(self):
        captcha_payload, response = self._get_captcha_payload()

        self.assertIn(captcha_payload['question_type'], QUESTION_TYPES)
        self.assertGreaterEqual(captcha_payload['first_number'], 0)
        self.assertLessEqual(captcha_payload['first_number'], 10)
        self.assertGreaterEqual(captcha_payload['second_number'], 0)
        self.assertLessEqual(captcha_payload['second_number'], 10)
        self.assertEqual(len(captcha_payload['display_items']), 4)
        self.assertEqual(
            sum(1 for item in captcha_payload['display_items'] if item['is_primary']),
            2
        )
        self.assertContains(response, get_question_text(captcha_payload['question_type']))

    def test_login_fails_with_wrong_captcha_answer(self):
        captcha_payload, _ = self._get_captcha_payload()
        wrong_answer = captcha_payload['answer'] + 1 if captcha_payload['answer'] < 20 else 19

        response = self._post_login(captcha_payload, captcha_answer=wrong_answer)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'پاسخ کپچا اشتباه است.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_fails_with_tampered_captcha_token(self):
        captcha_payload, _ = self._get_captcha_payload()

        response = self._post_login(captcha_payload, captcha_token='invalid-token')

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'کپچا منقضی شده است. دوباره تلاش کن.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_fails_with_wrong_password_even_with_correct_captcha(self):
        captcha_payload, _ = self._get_captcha_payload()

        response = self._post_login(captcha_payload, password='wrong-password')

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'نام کاربری یا رمز عبور اشتباه است.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_shows_persian_error_for_missing_captcha_answer(self):
        captcha_payload, _ = self._get_captcha_payload()
        response = self._post_login(captcha_payload, captcha_answer='')

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'captcha_answer', 'پاسخ کپچا را وارد کن.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_succeeds_with_correct_credentials_and_captcha(self):
        captcha_payload, _ = self._get_captcha_payload()

        response = self._post_login(captcha_payload)

        self.assertRedirects(response, self.home_url)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertIsNone(self.client.session.get(LOGIN_CAPTCHA_SESSION_KEY))

    def test_captcha_regenerates_after_failed_attempt(self):
        first_captcha, _ = self._get_captcha_payload()
        wrong_answer = first_captcha['answer'] + 1 if first_captcha['answer'] < 20 else 19

        response = self._post_login(first_captcha, captcha_answer=wrong_answer)

        second_captcha = self.client.session.get(LOGIN_CAPTCHA_SESSION_KEY)
        self.assertIsNotNone(second_captcha)
        self.assertNotEqual(first_captcha['token'], second_captcha['token'])
        self.assertContains(response, get_question_text(second_captcha['question_type']))


class CaptchaGeneratorTests(TestCase):
    @patch('account.captcha.random.shuffle', lambda items: None)
    @patch('account.captcha.random.choice', return_value=QUESTION_TYPE_SUM)
    @patch('account.captcha.random.randint', side_effect=[3, 7, 1, 2])
    def test_sum_question_uses_addition_answer(self, *_):
        captcha_payload = build_login_captcha()

        self.assertEqual(captcha_payload['question_type'], QUESTION_TYPE_SUM)
        self.assertEqual(captcha_payload['answer'], 10)
        self.assertEqual(captcha_payload['display_items'][0]['value'], 3)
        self.assertEqual(captcha_payload['display_items'][1]['value'], 7)
        self.assertTrue(captcha_payload['display_items'][0]['is_primary'])
        self.assertTrue(captcha_payload['display_items'][1]['is_primary'])

    @patch('account.captcha.random.shuffle', lambda items: None)
    @patch('account.captcha.random.choice', return_value=QUESTION_TYPE_MIN)
    @patch('account.captcha.random.randint', side_effect=[9, 2, 1, 2])
    def test_min_question_uses_smaller_number_answer(self, *_):
        captcha_payload = build_login_captcha()

        self.assertEqual(captcha_payload['question_type'], QUESTION_TYPE_MIN)
        self.assertEqual(captcha_payload['answer'], 2)
        self.assertEqual(captcha_payload['display_items'][0]['value'], 9)
        self.assertEqual(captcha_payload['display_items'][1]['value'], 2)
