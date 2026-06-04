from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.errors import AnsibleFilterError

from ansible_collections.example.proxmox.plugins.filter.proxmox2dict import (
    proxmox2dict,
)


def test_basic_vm():

    vm = {
        "agent": "1",
        "memory": "2048",
        "name": "generic-vm",
        "meta": "creation-qemu=10.0.0,ctime=1700000000",
        "tags": "managed;linux;example",
        "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr100,firewall=0",
        "scsi0": "STORAGE_POOL:vm-100-disk-0.qcow2,size=40G",
        "scsihw": "virtio-scsi-pci",
    }

    result = proxmox2dict(vm)

    assert result["parsed"]["metadata"]["agent"] == 1
    assert result["parsed"]["metadata"]["memory"] == 2048

    assert result["parsed"]["metadata"]["tags"] == [
        "managed",
        "linux",
        "example",
    ]

    assert result["parsed"]["storage"]["disks"]["scsi0"]["storage"] == "STORAGE_POOL"

    assert (
        result["parsed"]["storage"]["disks"]["scsi0"]["volume"]
        == "vm-100-disk-0.qcow2"
    )

    assert (
        result["parsed"]["storage"]["disks"]["scsi0"]["size"]
        == "40G"
    )


def test_network_parsing():

    vm = {
        "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr100,firewall=0",
        "net1": "e1000=AA:BB:CC:DD:EE:02,bridge=vmbr200",
    }

    result = proxmox2dict(vm)

    net0 = result["parsed"]["network"]["net_dict"]["net0"]

    assert net0["type"] == "virtio"
    assert net0["mac"] == "AA:BB:CC:DD:EE:01"
    assert net0["bridge"] == "vmbr100"

    net1 = result["parsed"]["network"]["net_dict"]["net1"]

    assert net1["type"] == "e1000"
    assert net1["mac"] == "AA:BB:CC:DD:EE:02"


def test_network_macless_views():

    vm = {
        "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr100,firewall=0"
    }

    result = proxmox2dict(vm)

    net = result["parsed"]["network"]["net_dict_macless"]["net0"]

    assert "mac" not in net
    assert net["type"] == "virtio"
    assert net["bridge"] == "vmbr100"

    net_list = result["parsed"]["network"]["net_list_macless"]

    assert len(net_list) == 1
    assert "mac" not in net_list[0]["net0"]


def test_multiple_disks():

    vm = {
        "scsi0": "FAST_STORAGE:vm-100-disk-0,size=40G",
        "scsi1": "FAST_STORAGE:vm-100-disk-1,size=80G",
        "sata0": "BACKUP_STORAGE:vm-100-backup,size=500G",
    }

    result = proxmox2dict(vm)

    disks = result["parsed"]["storage"]["disks"]

    assert len(disks) == 3

    assert disks["scsi0"]["size"] == "40G"
    assert disks["scsi1"]["size"] == "80G"
    assert disks["sata0"]["size"] == "500G"


def test_meta_parsing():

    vm = {
        "meta": "creation-qemu=10.0.0,ctime=1700000000"
    }

    result = proxmox2dict(vm)

    meta = result["parsed"]["metadata"]["meta"]

    assert meta["creation-qemu"] == "10.0.0"
    assert meta["ctime"] == "1700000000"


def test_empty_tags():

    vm = {
        "tags": ""
    }

    result = proxmox2dict(vm)

    assert result["parsed"]["metadata"]["tags"] == []


def test_ignore_scsihw():

    vm = {
        "scsihw": "virtio-scsi-pci",
        "scsi0": "LOCAL:disk,size=10G",
    }

    result = proxmox2dict(vm)

    assert "scsihw" not in result["parsed"]["metadata"]

    assert (
        result["parsed"]["storage"]["disks"]["scsi0"]["size"]
        == "10G"
    )


def test_build_netconfig_false():

    vm = {
        "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr100"
    }

    result = proxmox2dict(
        vm,
        build_netconfig=False,
    )

    assert result["parsed"]["network"] == {}


def test_invalid_input_list():

    with pytest.raises(AnsibleFilterError):
        proxmox2dict(["a", "b", "c"])


def test_invalid_input_string():

    with pytest.raises(AnsibleFilterError):
        proxmox2dict("not-a-dict")


def test_invalid_network_type():

    vm = {
        "net0": 12345
    }

    with pytest.raises(AnsibleFilterError):
        proxmox2dict(vm)


def test_invalid_storage_type():

    vm = {
        "scsi0": 12345
    }

    with pytest.raises(AnsibleFilterError):
        proxmox2dict(vm)


def test_empty_dict():

    result = proxmox2dict({})

    assert result == {
        "parsed": {
            "metadata": {},
            "storage": {
                "disks": {}
            },
            "network": {
                "net_dict": {},
                "net_list": [],
                "net_dict_macless": {},
                "net_list_macless": [],
            },
        }
    }
