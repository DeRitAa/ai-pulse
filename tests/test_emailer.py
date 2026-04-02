from unittest.mock import patch, MagicMock, call
from src.emailer import send_email, build_subject


class TestBuildSubject:
    def test_morning_format(self):
        subject = build_subject(report_time="2026-04-01 10:00", total_articles=35)
        assert "4月1日" in subject
        assert "上午版" in subject
        assert "35条" in subject

    def test_evening_format(self):
        subject = build_subject(report_time="2026-04-01 22:00", total_articles=47)
        assert "4月1日" in subject
        assert "晚间版" in subject
        assert "47条" in subject


class TestSendEmail:
    @patch("src.emailer.smtplib.SMTP")
    def test_sends_via_smtp(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            html_body="<html><body>test</body></html>",
            subject="Test Subject",
            from_addr="sender@gmail.com",
            to_addrs=["recipient@gmail.com"],
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            password="test-password",
        )

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("sender@gmail.com", "test-password")
        mock_smtp.sendmail.assert_called_once()

    @patch("src.emailer.smtplib.SMTP")
    def test_sends_to_multiple_recipients(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            html_body="<html>test</html>",
            subject="Test",
            from_addr="sender@gmail.com",
            to_addrs=["a@gmail.com", "b@gmail.com"],
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            password="pw",
        )

        args = mock_smtp.sendmail.call_args
        assert args[0][1] == ["a@gmail.com", "b@gmail.com"]
