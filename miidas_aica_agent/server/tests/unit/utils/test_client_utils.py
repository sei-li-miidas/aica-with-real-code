from unittest.mock import MagicMock
from utils.client_utils import get_client_ip


class TestGetClientIp:
    def test_get_ip_from_x_forwarded_for(self):
        """
        X-Forwarded-Forヘッダーがある場合（ALB経由など）
        """
        mock_request = MagicMock()
        # 複数のIPがある場合は先頭を取得する
        mock_request.headers.get.return_value = "10.0.0.1, 192.168.1.1"

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_get_ip_from_client_host(self):
        """
        X-Forwarded-Forがなく、client.hostがある場合
        """
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "192.168.1.50"

        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.50"

    def test_get_ip_unknown(self):
        """
        いずれも取得できない場合
        """
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client = None

        ip = get_client_ip(mock_request)
        assert ip == "Unknown"
