#include <core.p4>
#include <v1model.p4>

typedef bit<128> IPv6Adderess;
typedef bit<48> EthernetAddress;

#define MAX_HOPS 20
const bit<8> PROTO_IPV6 = 41;
const bit<8> PROTO_SRV6 = 43;

header ethernet_t{
    EthernetAddress dst_addr;
    EthernetAddress src_addr;
    bit<16> ether_type;
}

header ipv6_t {
    bit<4> version;
    bit<8> traffic_class;
    bit<20> flow_label;
    bit<16> payload_len;
    bit<8> next_hdr;
    bit<8> hop_limit;
    IPv6Adderess src_addr;
    IPv6Adderess dst_addr;
}

header srv6h_t {
    bit<8> next_hdr;
    bit<8> hdr_ext_len;
    bit<8> routing_type;
    bit<8> segment_left;
    bit<8> last_entry;
    bit<8> flags;
    bit<16> tag;
}

header srv6_list_t {
    bit<128> segment_id;
}


struct headers_t {
    ethernet_t ethernet;
    ipv6_t ipv6;
    ipv6_t ipv6_inner;
    srv6h_t srv6h;
    srv6_list_t[MAX_HOPS] srv6_list;
}

struct metadata_t {

}

parser my_parser(packet_in packet, out headers_t hd, inout metadata_t meta, inout standard_metadata_t standard_meta) {
    state start {
        packet.extract(hd.ethernet);
        transition select(hd.ethernet.ether_type) {
            0x86DD : parse_ipv6;
            default: accept;
        }
    }

    state parse_ipv6 {
        packet.extract(hd.ipv6);
        transition accept;
    }
}
control my_deparser(packet_out packet,
                   in headers_t hdr)
{
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv6);
        packet.emit(hdr.srv6h);
        packet.emit(hdr.srv6_list);
        packet.emit(hdr.ipv6_inner);

        
    }
}

control my_verify_checksum(inout headers_t hdr,
                         inout metadata_t meta)
{
    apply { }
}

control my_compute_checksum(inout headers_t hdr,
                          inout metadata_t meta)
{
    apply { }
}

control my_ingress(inout headers_t hdr,
                  inout metadata_t meta,
                  inout standard_metadata_t standard_metadata){
    bool dropped = false;

    action drop_action(){
        mark_to_drop(standard_metadata);
        dropped = true;
    }

    // action to_port_action(bit<9> port) {
    //     hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    //     standard_metadata.egress_spec = port;
    // }

    action fwd_ndp(bit<9> port) {
        standard_metadata.egress_spec = port;
    }

    action srv6_encap(bit<9> port, IPv6Adderess src_addr, IPv6Adderess s1, IPv6Adderess s2) {
        hdr.ipv6_inner.setValid();

        hdr.ipv6_inner.version = 6;
        hdr.ipv6_inner.traffic_class = hdr.ipv6.traffic_class;
        hdr.ipv6_inner.flow_label = hdr.ipv6.flow_label;
        hdr.ipv6_inner.payload_len = hdr.ipv6.payload_len;
        hdr.ipv6_inner.next_hdr = hdr.ipv6.next_hdr;
        hdr.ipv6_inner.hop_limit = hdr.ipv6.hop_limit;
        hdr.ipv6_inner.src_addr = hdr.ipv6.src_addr;
        hdr.ipv6_inner.dst_addr = hdr.ipv6.dst_addr;

        hdr.ipv6.payload_len = hdr.ipv6.payload_len + 40 + 24;
        hdr.ipv6.next_hdr = PROTO_SRV6;
        hdr.ipv6.src_addr = src_addr;
        hdr.ipv6.dst_addr = s1;

        hdr.srv6h.setValid();
        hdr.srv6h.next_hdr = PROTO_IPV6;
        hdr.srv6h.hdr_ext_len = 0x2;
        hdr.srv6h.routing_type = 0x4;
        hdr.srv6h.segment_left = 0;
        hdr.srv6h.last_entry = 0;
        hdr.srv6h.flags = 0;
        hdr.srv6h.tag = 0;

        hdr.srv6_list[0].setValid();
        hdr.srv6_list[0].segment_id = s2;

        standard_metadata.egress_spec = port;
    }

    // table ipv6_match {
    //     key = {
    //         hdr.ipv6.dst_addr: lpm;
    //     }

    //     actions = {
    //         drop_action;
    //         to_port_action;
    //     }
        
    //     size = 1024;
    //     default_action = drop_action;
    // }

    table ndp_match {
        actions = {
            fwd_ndp;
            NoAction();
        }
        key = {
        hdr.ipv6.src_addr: lpm;
        }
        size = 1024;
        default_action = NoAction();
    }
    
                  

    table srv6_match{
        actions = {
            srv6_encap;
            NoAction;
        }
        key = {
            hdr.ipv6.src_addr: lpm;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
        srv6_match.apply();
        ndp_match.apply();
    }
}

control my_egress(inout headers_t hdr,
                 inout metadata_t meta,
                 inout standard_metadata_t standard_metadata)
{
    apply { }
}

V1Switch(my_parser(),
         my_verify_checksum(),
         my_ingress(),
         my_egress(),
         my_compute_checksum(),
         my_deparser()) main;
