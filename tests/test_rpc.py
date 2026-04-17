import unittest

from app.rpc import RpcGet


class RpcGetStub(RpcGet):
    def __init__(self, responses):
        super().__init__("http://127.0.0.1:8114", 5, [])
        self.responses = responses

    def _call(self, _rpc_id, method, _params):
        return self.responses.get(method)


class RpcGetTest(unittest.TestCase):
    def test_get_tip_economics_parses_dao(self):
        rpc = RpcGetStub(
            {
                "get_tip_header": {
                    "dao": "0xb5a3e047474401001bc476b9ee573000c0c387962a38000000febffacf030000"
                }
            }
        )
        economics = rpc.get_tip_economics()
        self.assertAlmostEqual(economics["total_issuance_ckb"], 3565479.15981749)
        self.assertAlmostEqual(economics["dao_deposit_ckb"], 617555.6526176)
        self.assertEqual(economics["occupied_capacity_ckb"], 41918.0)

    def test_get_consensus_epoch_duration_target(self):
        rpc = RpcGetStub({"get_consensus": {"epoch_duration_target": "0x3840"}})
        consensus = rpc.get_consensus()
        self.assertEqual(consensus["epoch_duration_target"], 14400)


if __name__ == "__main__":
    unittest.main()
