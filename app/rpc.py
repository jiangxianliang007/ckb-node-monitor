from __future__ import annotations

import logging
import struct
import time
from collections.abc import Mapping

import requests

from .utils import convert_int

logger = logging.getLogger(__name__)
SHANNONS_PER_CKB = 100_000_000


class RpcGet:
    def __init__(self, rpc_url: str, timeout: int, bootnodes: list[str]) -> None:
        self.rpc_url = rpc_url
        self.timeout = timeout
        self.bootnodes = bootnodes
        self.session = requests.Session()

    def _call(self, rpc_id: int, method: str, params: list[object]) -> Mapping[str, object] | None:
        payload = {"id": rpc_id, "jsonrpc": "2.0", "method": method, "params": params}
        try:
            response = self.session.post(
                url=self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if "result" not in data:
                logger.warning("RPC method %s missing result: %s", method, data)
                return None
            result = data["result"]
            if isinstance(result, Mapping):
                return result
            return {"value": result}
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("RPC method %s failed: %s", method, exc)
            return None

    def get_LastBlockInfo(self) -> dict[str, int | str]:
        replay = self._call(2, "get_tip_header", [])
        if not replay:
            return {"last_blocknumber": -1, "last_block_hash": "-1", "last_block_timestamp": -1}
        return {
            "last_blocknumber": convert_int(str(replay.get("number", "-1"))),
            "last_block_hash": str(replay.get("hash", "-1")),
            "last_block_timestamp": convert_int(str(replay.get("timestamp", "-1"))),
        }

    def get_tip_economics(self) -> dict[str, float]:
        replay = self._call(2, "get_tip_header", [])
        if not replay:
            return {
                "total_issuance_ckb": -1.0,
                "dao_deposit_ckb": -1.0,
                "occupied_capacity_ckb": -1.0,
            }

        dao_raw = str(replay.get("dao", ""))
        dao_hex = dao_raw[2:] if dao_raw.startswith("0x") else dao_raw
        if len(dao_hex) != 64:
            return {
                "total_issuance_ckb": -1.0,
                "dao_deposit_ckb": -1.0,
                "occupied_capacity_ckb": -1.0,
            }

        try:
            dao_bytes = bytes.fromhex(dao_hex)
            total_issuance = struct.unpack("<Q", dao_bytes[0:8])[0]
            dao_deposit = struct.unpack("<Q", dao_bytes[16:24])[0]
            occupied_capacity = struct.unpack("<Q", dao_bytes[24:32])[0]
            return {
                "total_issuance_ckb": total_issuance / SHANNONS_PER_CKB,
                "dao_deposit_ckb": dao_deposit / SHANNONS_PER_CKB,
                "occupied_capacity_ckb": occupied_capacity / SHANNONS_PER_CKB,
            }
        except (ValueError, TypeError, struct.error):
            return {
                "total_issuance_ckb": -1.0,
                "dao_deposit_ckb": -1.0,
                "occupied_capacity_ckb": -1.0,
            }

    def get_LastPoolInfo(self) -> dict[str, int]:
        replay = self._call(2, "tx_pool_info", [])
        if not replay:
            return {
                "total_tx_cycles": -1,
                "total_tx_size": -1,
                "orphan": -1,
                "pending": -1,
                "proposed": -1,
                "verify_queue_size": -1,
            }
        return {
            "total_tx_cycles": convert_int(str(replay.get("total_tx_cycles", "-1"))),
            "total_tx_size": convert_int(str(replay.get("total_tx_size", "-1"))),
            "orphan": convert_int(str(replay.get("orphan", "-1"))),
            "pending": convert_int(str(replay.get("pending", "-1"))),
            "proposed": convert_int(str(replay.get("proposed", "-1"))),
            "verify_queue_size": convert_int(str(replay.get("verify_queue_size", "0"))),
        }

    def get_BlockSize(self, block_hash: str) -> dict[str, int]:
        replay = self._call(42, "get_block", [block_hash, "0x0"])
        if not replay:
            return {"block_size": -1}
        return {"block_size": len(str(replay.get("value", "")))}

    def get_BlockDetail(self, block_hash: str) -> dict[str, int | str]:
        replay = self._call(2, "get_block", [block_hash])
        if not replay:
            return {
                "commit_transactions": -1,
                "blocknumber_timestamp": -1,
                "proposal_transactions": -1,
                "uncles": -1,
                "client_version": "-1",
            }

        try:
            transactions = replay.get("transactions", [])
            proposals = replay.get("proposals", [])
            uncles = replay.get("uncles", [])
            header = replay.get("header", {})

            client_version = "none"
            if transactions:
                first_tx = transactions[0]
                first_witness = first_tx.get("witnesses", [""])[0]
                messages = first_witness[2:]
                messages_d = bytes.fromhex(messages)
                start = struct.unpack("<I", messages_d[8:12])[0]
                total = int(struct.unpack("<I", messages_d[4:8])[0] / 4 - 1)
                if total != 2:
                    end = struct.unpack("<I", messages_d[12:16])[0]
                    message = messages_d[start:end][4:].decode("latin-1")
                else:
                    message = messages_d[start:][4:].decode("latin-1")
                parts = message.split(" ")
                if len(parts) > 1 and len(parts[1]) > 5:
                    client_version = parts[1]

            return {
                "commit_transactions": len(transactions),
                "blocknumber_timestamp": convert_int(str(header.get("timestamp", "-1"))),
                "proposal_transactions": len(proposals),
                "uncles": len(uncles),
                "client_version": client_version,
            }
        except (ValueError, TypeError, IndexError, struct.error) as exc:
            logger.warning("Failed parsing block detail: %s", exc)
            return {
                "commit_transactions": -1,
                "blocknumber_timestamp": -1,
                "proposal_transactions": -1,
                "uncles": -1,
                "client_version": "-1",
            }

    def get_node_info(self) -> dict[str, int | str]:
        replay = self._call(2, "local_node_info", [])
        if not replay:
            return {"node_address": "-1", "node_id": "-1", "node_version": "-1", "node_status": 0}
        addresses = replay.get("addresses", [])
        address = "-1"
        if addresses:
            address = str(addresses[0].get("address", "-1"))
        return {
            "node_address": address,
            "node_id": str(replay.get("node_id", "-1")),
            "node_version": str(replay.get("version", "-1")),
            "node_status": 1,
        }

    def get_block_hash(self, blocknumber: int) -> dict[str, str]:
        replay = self._call(2, "get_block_hash", [f"0x{blocknumber:x}"])
        if not replay:
            return {"blocknumber_hash": "-1"}
        return {"blocknumber_hash": str(replay.get("value", "-1"))}

    def get_peer_count(self) -> dict[str, int]:
        replay = self._call(2, "get_peers", [])
        peers = []
        if replay and "value" in replay and isinstance(replay["value"], list):
            peers = replay["value"]
        if not peers:
            return {"peer_inbound": -1, "peer_outbound": -1, "light_clients": -1}

        peer_outbound = len([peer for peer in peers if peer.get("is_outbound")])
        lightclientversion = []
        for peer in peers:
            version = str(peer.get("version", "unknown"))
            if version == "unknown":
                continue
            try:
                minor = int(version.split(".")[1])
                if minor < 100:
                    lightclientversion.append(minor)
            except (ValueError, IndexError):
                continue

        return {
            "peer_inbound": len(peers) - peer_outbound,
            "peer_outbound": peer_outbound,
            "light_clients": len(lightclientversion),
        }

    def get_current_epoch(self) -> dict[str, int]:
        replay = self._call(42, "get_current_epoch", [])
        if not replay:
            return {"length": -1, "start_number": -1}
        return {
            "length": convert_int(str(replay.get("length", "-1"))),
            "start_number": convert_int(str(replay.get("start_number", "-1"))),
        }

    def get_banned_addresses(self) -> dict[str, int]:
        replay = self._call(42, "get_banned_addresses", [])
        nowtime = int(round(time.time() * 1000))
        records = []
        if replay and "value" in replay and isinstance(replay["value"], list):
            records = replay["value"]
        if replay is None:
            return {"ban_all": -1, "ban_bootnode": -1}

        bootnode_ban = []
        for record in records:
            try:
                banip = str(record.get("address", "")).split("/")[0]
                ban_until = int(str(record.get("ban_until", "0")), 0)
                if nowtime > ban_until:
                    continue
                if banip:
                    bootnode_ban.append(banip)
            except (ValueError, TypeError):
                continue

        intersection_count = len([value for value in self.bootnodes if value in bootnode_ban])
        return {"ban_bootnode": intersection_count, "ban_all": len(bootnode_ban)}

    def get_pending_tx(self) -> dict[str, int | str | float]:
        replay = self._call(42, "get_raw_tx_pool", [True])
        if not replay:
            return {
                "pending_tx_count": -1,
                "first_pending_tx_hash": "-1",
                "first_pending_tx_time": -1,
                "max_ancestors_count": -1,
            }

        pending = replay.get("pending", {})
        if not isinstance(pending, dict):
            return {
                "pending_tx_count": -1,
                "first_pending_tx_hash": "-1",
                "first_pending_tx_time": -1,
                "max_ancestors_count": -1,
            }

        tx_count = len(pending)
        if tx_count == 0:
            return {
                "pending_tx_count": 0,
                "first_pending_tx_hash": "-1",
                "first_pending_tx_time": 0,
                "max_ancestors_count": 0,
            }

        nowtime = int(round(time.time() * 1000))
        try:
            min_key, min_timestamp = min(
                ((key, int(str(entry["timestamp"]), 16)) for key, entry in pending.items() if "timestamp" in entry),
                key=lambda item: item[1],
            )
            pending_tx_seconds = (nowtime - min_timestamp) / 1000
            max_ancestors_count = max(
                int(str(transaction.get("ancestors_count", "0x0")), 16) for transaction in pending.values()
            )
            return {
                "pending_tx_count": tx_count,
                "first_pending_tx_hash": min_key,
                "first_pending_tx_time": pending_tx_seconds,
                "max_ancestors_count": max_ancestors_count,
            }
        except (ValueError, TypeError) as exc:
            logger.warning("Failed parsing pending tx stats: %s", exc)
            return {
                "pending_tx_count": tx_count,
                "first_pending_tx_hash": "-1",
                "first_pending_tx_time": -1,
                "max_ancestors_count": -1,
            }

    def get_fee_rate_statistics(self) -> dict[str, int]:
        replay = self._call(42, "get_fee_rate_statistics", [])
        if not replay:
            return {"mean": -1, "median": -1}
        return {
            "mean": convert_int(str(replay.get("mean", "-1"))),
            "median": convert_int(str(replay.get("median", "-1"))),
        }

    def estimate_fee_rate(self) -> dict[str, int]:
        replay = self._call(42, "estimate_fee_rate", ["no_priority", True])
        if not replay:
            return {"estimate_fee_rate": -1}
        return {"estimate_fee_rate": convert_int(str(replay.get("value", "-1")))}

    def get_difficulty(self) -> dict[str, int]:
        replay = self._call(42, "get_blockchain_info", [])
        if not replay:
            return {"difficulty": -1}
        return {"difficulty": convert_int(str(replay.get("difficulty", "-1")))}

    def get_consensus(self) -> dict[str, int]:
        replay = self._call(42, "get_consensus", [])
        if not replay:
            return {"epoch_duration_target": -1}
        return {"epoch_duration_target": convert_int(str(replay.get("epoch_duration_target", "-1")))}
