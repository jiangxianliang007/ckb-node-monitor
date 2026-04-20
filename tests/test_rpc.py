import unittest
import struct

from app.rpc import RpcGet


class RpcGetStub(RpcGet):
    def __init__(self, responses):
        super().__init__("http://127.0.0.1:8114", 5, [])
        self.responses = responses

    def _call(self, _rpc_id, method, _params):
        response = self.responses.get(method)
        if isinstance(response, list):
            if not response:
                return None
            return response.pop(0)
        return response


class RpcGetTest(unittest.TestCase):
    def test_get_last_block_info_parses_occupied_capacity_from_dao(self):
        occupied_capacity_ckb = 19800000000.0
        occupied_capacity_shannons = int(occupied_capacity_ckb * 100_000_000)
        dao_bytes = b"\x00" * 24 + struct.pack("<Q", occupied_capacity_shannons)
        rpc = RpcGetStub(
            {
                "get_tip_header": {
                    "number": "0x123",
                    "hash": "0xtiphash",
                    "timestamp": "0x456",
                    "dao": "0x" + dao_bytes.hex(),
                }
            }
        )
        last_block = rpc.get_LastBlockInfo()
        self.assertEqual(last_block["last_blocknumber"], 291)
        self.assertEqual(last_block["last_block_hash"], "0xtiphash")
        self.assertEqual(last_block["last_block_timestamp"], 1110)
        self.assertEqual(last_block["occupied_capacity"], occupied_capacity_ckb)

    def test_get_last_block_info_error_includes_occupied_capacity_default(self):
        rpc = RpcGetStub({"get_tip_header": None})
        last_block = rpc.get_LastBlockInfo()
        self.assertEqual(last_block["occupied_capacity"], -1.0)

    def test_get_dao_statistics_from_rich_indexer(self):
        first_page = [{"output": {"lock": {"code_hash": "0x1", "hash_type": "type", "args": "0xabc"}}} for _ in range(100)]
        second_page = [
            {"output": {"lock": {"code_hash": "0x1", "hash_type": "type", "args": "0xabc"}}},
            {"output": {"lock": {"code_hash": "0x2", "hash_type": "type", "args": "0xdef"}}},
        ]
        rpc = RpcGetStub(
            {
                "get_consensus": {"epoch_duration_target": "0x3840", "dao_type_hash": "0xdao_hash"},
                "get_cells_capacity": {"capacity": "0x2540be400"},
                "get_cells": [{"objects": first_page, "last_cursor": "0xcursor"}, {"objects": second_page, "last_cursor": "0xend"}],
            }
        )
        statistics = rpc.get_dao_statistics()
        self.assertEqual(statistics["dao_deposit_ckb"], 100.0)
        self.assertEqual(statistics["dao_depositors_count"], 2.0)

    def test_get_consensus_epoch_duration_target(self):
        rpc = RpcGetStub({"get_consensus": {"epoch_duration_target": "0x3840", "dao_type_hash": "0xdao_hash"}})
        consensus = rpc.get_consensus()
        self.assertEqual(consensus["epoch_duration_target"], 14400)
        self.assertEqual(consensus["dao_type_hash"], "0xdao_hash")

    def test_get_dao_statistics_handles_missing_rich_indexer(self):
        rpc = RpcGetStub({"get_consensus": {"epoch_duration_target": "0x3840", "dao_type_hash": "0xdao_hash"}})
        statistics = rpc.get_dao_statistics()
        self.assertEqual(statistics["dao_deposit_ckb"], -1.0)
        self.assertEqual(statistics["dao_depositors_count"], -1.0)


if __name__ == "__main__":
    unittest.main()
