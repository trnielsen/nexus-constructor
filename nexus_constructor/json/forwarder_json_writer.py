from typing import List, TextIO

import h5py

from nexus_constructor.common_attrs import CommonAttrs
from nexus_constructor.json.helpers import object_to_json_file
from nexus_constructor.nexus.nexus_wrapper import get_nx_class
from nexus_constructor.writer_modules import WriterModules

FORWARDER_SCHEMAS = [WriterModules.F142.value, WriterModules.TDCTIME.value]


def find_forwarder_streams(root, provider_type: str, default_broker: str) -> List:
    """
    Find all streams and return them in the expected format for JSON serialisiation.
    :return: A dictionary of stream groups, with their respective field names and values.
    """
    pv_names = {}
    stream_list = []

    def find_streams(_, node):
        nonlocal pv_names
        nonlocal stream_list
        if (
            isinstance(node, h5py.Group)
            and get_nx_class(node) == CommonAttrs.NC_STREAM
            and node["writer_module"][()] in FORWARDER_SCHEMAS
        ):
            writer_module = node["writer_module"][()]
            pv_name = node["source"][()]
            if pv_name not in pv_names.keys():
                stream_list.append(
                    {
                        "channel": pv_name,
                        "converter": get_converter(node, writer_module),
                        "channel_provider_type": provider_type,
                    }
                )
                pv_names[pv_name] = len(stream_list)
            else:
                duplicated_stream = stream_list[pv_names[pv_name] - 1]
                new_stream_converter = get_converter(node, writer_module)
                if isinstance(duplicated_stream["converter"], list):
                    duplicated_stream["converter"].append(new_stream_converter)
                elif isinstance(duplicated_stream["converter"], dict):
                    duplicated_stream["converter"] = [
                        duplicated_stream["converter"],
                        new_stream_converter,
                    ]

    def get_converter(node, writer_module):
        return {"schema": writer_module, "topic": get_topic(node)}

    def get_topic(node):
        uri = node["topic"][()]
        uri_split = uri.split("/")
        if len(uri_split) == 1:
            # Broker is not already included in the topic string, so add the default broker
            broker = f"{default_broker}/" if default_broker else ""
            return f"{broker}{uri}"
        return uri

    root.visititems(find_streams)
    return stream_list


def generate_forwarder_command(
    output_file: TextIO, root: h5py.Group, provider_type: str, default_broker: str
):
    """
    Generate a forwarder command containing a list of PVs and which topics to route them to.
    :param output_file: file object to write the JSON output to.
    :param streams: dictionary of stream objects.
    :param provider_type: whether to use channel access or pv access protocol
    """
    tree_dict = {"streams": find_forwarder_streams(root, provider_type, default_broker)}
    object_to_json_file(tree_dict, output_file)
