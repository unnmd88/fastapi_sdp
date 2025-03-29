from sdp_lib.management_controllers.snmp.host_properties import HostProtocolData


def build_class_attrs(props: HostProtocolData):
    def real_decorator(a_class):
        def wrapper(*args, **kwargs):
            a_class.host_properties = props
            a_class.type_controller = props.type_controller
            a_class.host_protocol = props.type_controller
            a_class.community_r = props.community_r
            a_class.community_w = props.community_w
            return a_class
        return wrapper
    return real_decorator