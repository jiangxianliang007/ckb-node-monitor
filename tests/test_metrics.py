import unittest

from prometheus_client import generate_latest

from app.metrics import MetricsCollector


class FakeRpcGet:
    def __init__(self) -> None:
        self._node_infos = [
            {"node_status": 1, "node_address": "/ip4/1.1.1.1", "node_id": "node-a", "node_version": "0.201.0"},
            {"node_status": 1, "node_address": "/ip4/2.2.2.2", "node_id": "node-b", "node_version": "0.202.0"},
        ]
        self._last_blocks = [
            {"last_blocknumber": 0, "last_block_timestamp": 1000, "last_block_hash": "hash-a"},
            {"last_blocknumber": 0, "last_block_timestamp": 2000, "last_block_hash": "hash-b"},
        ]
        self._block_hashes = [{"blocknumber_hash": "hash-a"}, {"blocknumber_hash": "hash-b"}]
        self._block_details = [
            {
                "commit_transactions": 1,
                "proposal_transactions": 1,
                "uncles": 0,
                "client_version": "0.201.0",
                "blocknumber_timestamp": 1000,
            },
            {
                "commit_transactions": 2,
                "proposal_transactions": 1,
                "uncles": 0,
                "client_version": "0.202.0",
                "blocknumber_timestamp": 2000,
            },
        ]
        self._node_info_i = 0
        self._last_block_i = 0
        self._block_hash_i = 0
        self._block_detail_i = 0

    @staticmethod
    def _next(sequence, index_name, instance):
        idx = getattr(instance, index_name)
        setattr(instance, index_name, min(idx + 1, len(sequence) - 1))
        return sequence[idx]

    def get_node_info(self):
        return self._next(self._node_infos, "_node_info_i", self)

    def get_peer_count(self):
        return {"peer_outbound": 1, "peer_inbound": 1, "light_clients": 0}

    def get_LastBlockInfo(self):
        return self._next(self._last_blocks, "_last_block_i", self)

    def get_block_hash(self, _block_number):
        return self._next(self._block_hashes, "_block_hash_i", self)

    def get_BlockDetail(self, _block_hash):
        return self._next(self._block_details, "_block_detail_i", self)

    def get_LastPoolInfo(self):
        return {
            "total_tx_size": 0,
            "total_tx_cycles": 0,
            "orphan": 0,
            "pending": 0,
            "proposed": 0,
            "verify_queue_size": 0,
        }

    def get_current_epoch(self):
        return {"start_number": 0, "length": 1}

    def get_banned_addresses(self):
        return {"ban_all": 0, "ban_bootnode": 0}

    def get_pending_tx(self):
        return {"first_pending_tx_time": 0, "pending_tx_count": 0, "max_ancestors_count": 0}

    def get_fee_rate_statistics(self):
        return {"mean": 0, "median": 0}

    def get_BlockSize(self, _block_hash):
        return {"block_size": 0}

    def estimate_fee_rate(self):
        return {"estimate_fee_rate": 0}

    def get_difficulty(self):
        return {"difficulty": 0}


class MetricsCollectorTest(unittest.TestCase):
    def test_collect_clears_stale_dynamic_label_series(self):
        collector = MetricsCollector(
            FakeRpcGet(),
            {
                "chain": "mainnet",
                "node_name": "test-node",
                "node_type": "public",
                "node_ip": "127.0.0.1",
                "node_location": "us-east-1",
            },
        )

        collector.collect()
        collector.collect()

        self.assertEqual(len(collector.Node_Get_LastBlockInfo._metrics), 1)
        self.assertEqual(len(collector.Node_Get_client_version._metrics), 1)
        self.assertEqual(len(collector.Node_Get_LocalInfo._metrics), 1)

        output = generate_latest(collector.registry).decode("utf-8")
        self.assertIn('block_hash="hash-b"', output)
        self.assertNotIn('block_hash="hash-a"', output)
        self.assertIn('client_version="0.202.0"', output)
        self.assertNotIn('client_version="0.201.0"', output)
        self.assertIn('node_id="node-b"', output)
        self.assertNotIn('node_id="node-a"', output)


if __name__ == "__main__":
    unittest.main()
