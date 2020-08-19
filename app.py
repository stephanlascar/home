import datetime

from flask import Flask, jsonify
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

MAX_SIGNED = 2147483648

application = Flask(__name__)


@application.route('/api/power-consumption/solar-panel')
def hello_world():
    client = ModbusTcpClient('192.168.0.4', retries=3, unit_id=3, timeout=1000)

    return jsonify(dict(
        date=datetime.datetime.fromtimestamp(_get_modbus_message(client, 30193, 2, 3).decode_32bit_int()).isoformat(),
        dc_current_input=_sanitize_modbus_value(_get_modbus_message(client, 30769, 2, 3).decode_32bit_uint()),
        dc_voltage_input=_sanitize_modbus_value(_get_modbus_message(client, 30771, 2, 3).decode_32bit_uint()),
        dc_power_input=_sanitize_modbus_value(_get_modbus_message(client, 30773, 2, 3).decode_32bit_uint()),
        power=_sanitize_modbus_value(_get_modbus_message(client, 30775, 2, 3).decode_32bit_uint()),
        day_yield=_sanitize_modbus_value(_get_modbus_message(client, 30535, 2, 3).decode_32bit_uint()),
        total_yield=_sanitize_modbus_value(_get_modbus_message(client, 30529, 2, 3).decode_32bit_uint())
    ))


def _get_modbus_message(client, adress, count, unit):
    data = client.read_holding_registers(adress, count, unit=unit)
    return BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big)


def _sanitize_modbus_value(value):
    return 0 if value == MAX_SIGNED else value
