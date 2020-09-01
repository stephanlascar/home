import datetime

from flask import Flask, jsonify
from flask_caching import Cache
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import kylin


MAX_SIGNED = 2147483648

application = Flask(__name__)
cache = Cache(application, config={'CACHE_TYPE': 'simple'})


@application.route('/api/power-consumption/solar-panel')
@cache.cached(timeout=60)
def solar_panel():
    client = ModbusTcpClient('192.168.0.4', retries=3, unit_id=3, timeout=1000)

    data = dict(
        date=datetime.datetime.fromtimestamp(_get_modbus_message(client, 30193, 2, 3).decode_32bit_int()).isoformat(),
        dc_current_input=_sanitize_modbus_value(_get_modbus_message(client, 30769, 2, 3).decode_32bit_uint()),
        dc_voltage_input=_sanitize_modbus_value(_get_modbus_message(client, 30771, 2, 3).decode_32bit_uint()),
        dc_power_input=_sanitize_modbus_value(_get_modbus_message(client, 30773, 2, 3).decode_32bit_uint()),
        power=_sanitize_modbus_value(_get_modbus_message(client, 30775, 2, 3).decode_32bit_uint()),
        day_yield=_sanitize_modbus_value(_get_modbus_message(client, 30535, 2, 3).decode_32bit_uint()),
        total_yield=_sanitize_modbus_value(_get_modbus_message(client, 30529, 2, 3).decode_32bit_uint())
    )
    client.close()
    return jsonify(data)


@application.route('/api/power-consumption/teleinfo')
@cache.cached(timeout=60)
def teleinfo():
    teleinfo = kylin.Kylin(timeout=2, port='/dev/ttyUSB0')
    teleinfo.open()
    frame = teleinfo.readframe()
    frame['WINST'] = frame['IINST'] * 234
    teleinfo.close()
    return jsonify({item['name']: item['value'] for item in frame})


def _get_modbus_message(client, adress, count, unit):
    data = client.read_holding_registers(adress, count, unit=unit)
    return BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big)


def _sanitize_modbus_value(value):
    return 0 if value == MAX_SIGNED else value
