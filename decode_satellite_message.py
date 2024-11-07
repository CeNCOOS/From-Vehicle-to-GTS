import json

class FieldInfo:
    def __init__(self, fieldName, min_val, max_val, precision, bits,unit):
        self.fieldName = fieldName
        self.min = min_val
        self.max = max_val
        self.precision = precision
        self.bits = bits
        self.unit = unit

    def calculateMaxValue(self):

        return self.min + (((1 << self.bits) - 1) * self.precision)


def load_format_from_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        bpFormat = [FieldInfo(**field) for field in data]
    return bpFormat



def get_bit(data, bit_index):
    byte_index = bit_index // 8
    bit_index_in_byte = bit_index % 8
    return (data[byte_index] >> (7 - bit_index_in_byte)) & 1

def get_bits(data, start_bit, bit_count):
    value = 0
    for i in range(bit_count):
        value <<= 1
        value |= get_bit(data, start_bit + i)
    return value

def unpack_data(data, bpFormat):
    unpacked_data = {}
    bit_index = 0
    expected_bits = sum(field.bits for field in bpFormat)
    expected_bytes = (expected_bits + 7) // 8  # Round up to the nearest byte

    if len(data) != expected_bytes:
        raise ValueError(f"Data length mismatch: received {len(data)} bytes, expected {expected_bytes} bytes.")

    for field in bpFormat:
        if field.bits == 0:
            break
        raw_value = get_bits(data, bit_index, field.bits)
        decoded_value = field.min + raw_value * field.precision
        unpacked_data[field.fieldName] = decoded_value
        bit_index += field.bits

    return unpacked_data

#this is the structure used to encode and decode the messages
#fieldName, min_val, max_val, precision, bits
# Load the message format from the JSON file
bpFormat = load_format_from_json('message_format2.json')

