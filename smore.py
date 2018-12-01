"""Layer2 Demo App
- Implements reactive forwarding for a vlan-aware layer 2 switch.
- Ignores LLDP packets.
- Does not support loops.
"""

#Reads yaml file
import yaml
stream = open('smore.yaml', 'r')
smore = yaml.load(stream)

import random
import zof
from zof.pktview import pktview_from_list

APP = zof.Application('layer2')

# The forwarding table is a dictionary that maps:
#   datapath_id -> { (eth_dst, vlan_vid) -> (out_port, time) }

APP.forwarding_table = {}

@APP.message('channel_up')
def channel_up(event):
    """Set up datapath when switch connects."""
    APP.logger.info('%s Connected from %s (%d ports, version %d)',
                    event['datapath_id'], event['endpoint'],
                    len(event['datapath']), event['version'])
    APP.logger.info('%s Remove all flows', event['datapath_id'])

    DELETE_FLOWS.send()
    BARRIER.send()
    TABLE_MISS_FLOW.send()


@APP.message('channel_down')
def channel_down(event):
    """Clean up when switch disconnects."""
    APP.logger.info('%s Disconnected', event['datapath_id'])
    APP.forwarding_table.pop(event['datapath_id'], None)


@APP.message('packet_in', eth_type=0x88cc)
def lldp_packet_in(_event):
    """Ignore lldp packets."""
    APP.logger.debug('lldp packet ignored')


host = 0


#function to swap between a variable number of rotational hosts 
def MTD_Swap(pkt_tcp, pkt_eth, external_port, dummy_mac, dummy_ip, internal_port, rotational):
     global host
     #alternates hosts
     if (smore['config']['random'] == True):
         host = random.randint(0, (len(smore['Rot'])-1))
     else:
         host+=1
         if (host==len(smore['Rot'])):
             host=0
     #gets the hostname to put into rotation from the counter
     hostname = list(rotational.keys())[host]
     print("HOST: %s" % host)
     #gets mac and IP based off of host to put into rotation
     internal_mac=smore['Rot'][hostname]['mac']
     internal_ip=smore['Rot'][hostname]['ip']

     SET_MTD_INCOMING_FLOW.send(
         match_ip_dst=dummy_ip,
         match_eth_src=pkt_eth,
         match_tcp_src=pkt_tcp,
         out_port=internal_port,
         eth_new_dst=internal_mac,
         ip_new_dst=internal_ip)

     SET_MTD_OUTGOING_FLOW.send(
         match_ip_src=internal_ip,
         match_eth_dst=pkt_eth,
         match_tcp_dst=pkt_tcp,
         out_port=external_port,
         eth_new_src=dummy_mac,
         ip_new_src=dummy_ip)


port_table = {}

@APP.message('packet_in')
def packet_in(event):
    """Handle incoming packets."""
    APP.logger.debug('packet in %r', event)
    datapath_id = event['datapath_id']
    msg = event['msg']
    time = event['time']
    data = msg['data']

    # Check for incomplete packet data.
    if len(data) < msg['total_len']:
        #APP.logger.warning('Incomplete packet data: %r', event)
        return

    in_port = msg['in_port']
    pkt = msg['pkt']
    vlan_vid = pkt('vlan_vid', default=0)

    # Retrieve fwd_table for this datapath.
    fwd_table = APP.forwarding_table.setdefault(datapath_id, {})

    # Update fwd_table based on eth_src and in_port.
    if (pkt.eth_src, vlan_vid) not in fwd_table:
        APP.logger.info('%s Learn %s vlan %s on port %s', datapath_id,
                        pkt.eth_src, vlan_vid, in_port)
        fwd_table[(pkt.eth_src, vlan_vid)] = (in_port, time)
        print("Putting %s on port %s" % (pkt.eth_src, in_port))
        port_table[in_port] = (pkt.eth_src, vlan_vid)


    # Lookup output port for eth_dst. If not found, set output port to 'ALL'.
    out_port, _ = fwd_table.get((pkt.eth_dst, vlan_vid), ('ALL', None))

    #calls rotation using yaml file 
    if pkt.eth_dst==smore['Dummy']['mac']:
        MTD_Swap(pkt.tcp_src, pkt.eth_src, smore['Ports']['external'], smore['Dummy']['mac'], smore['Dummy']['ip'], smore['Ports']['internal'], smore['Rot'])
    #extra flow from the host machine in case a flow expires while one is initialized
    for host in smore['Rot']:
        if pkt.eth_src==smore['Rot'][host]['mac']:
            DELETE_FLOWS.send()
            BARRIER.send()
            TABLE_MISS_FLOW.send()
            MTD_Swap(pkt.tcp_dst, pkt.eth_dst, smore['Ports']['external'], smore['Dummy']['mac'], smore['Dummy']['ip'], smore['Ports']['internal'], smore['Rot'])

@APP.message('flow_removed')
def flow_removed(event):
    """Handle flow removed message."""
    datapath_id = event['datapath_id']
    match = pktview_from_list(event['msg']['match'])
    try:
        vlan_vid = match.vlan_vid
    except:
        vlan_vid=0
    reason = event['msg']['reason']

    fwd_table = APP.forwarding_table.get(datapath_id)
    try:
        if fwd_table:
           eth_dst=match.eth_dst
           fwd_table.pop((eth_dst, vlan_vid), None)
    except:
        eth_dst=0
        pass

    APP.logger.info('%s Remove %s vlan %s (%s)', datapath_id, eth_dst,
                    vlan_vid, reason)


@APP.message(any)
def other_message(event):
    """Log ignored messages."""
    APP.logger.debug('Ignored message: %r', event)


DELETE_FLOWS = zof.compile('''
  # Delete flows in table 0.
  type: FLOW_MOD
  msg:
    command: DELETE
    table_id: 0
''')

BARRIER = zof.compile('''
  type: BARRIER_REQUEST
''')

TABLE_MISS_FLOW = zof.compile('''
  # Add permanent table miss flow entry to table 0
  type: FLOW_MOD
  msg:
    command: ADD
    table_id: 0
    priority: 0
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: OUTPUT
            port_no: CONTROLLER
            max_len: NO_BUFFER
''')

LEARN_MAC_FLOW = zof.compile('''
  type: FLOW_MOD
  msg:
    table_id: 0
    command: ADD
    idle_timeout: 60
    hard_timeout: 120
    priority: 10
    buffer_id: NO_BUFFER
    flags: [ SEND_FLOW_REM ]
    match:
      - field: ETH_DST
        value: $eth_dst
      - field: VLAN_VID
        value: $vlan_vid
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: OUTPUT
            port_no: $out_port
            max_len: MAX
''')


SET_MTD_INCOMING_FLOW = zof.compile('''
  type: FLOW_MOD
  msg:
    table_id: 0
    command: ADD
    idle_timeout: 6
    hard_timeout: 0
    priority: 100
    buffer_id: NO_BUFFER
    flags: [ SEND_FLOW_REM ]
    match:
      - field: IPV4_DST
        value: $match_ip_dst
      - field: ETH_SRC
        value: $match_eth_src
      - field: TCP_SRC
        value: $match_tcp_src
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: SET_FIELD
            field: ETH_DST
            value: $eth_new_dst
          - action: SET_FIELD
            field: IPV4_DST
            value: $ip_new_dst
          - action: OUTPUT
            port_no: $out_port
            max_len: MAX
''')

SET_MTD_OUTGOING_FLOW = zof.compile('''
  type: FLOW_MOD
  msg:
    table_id: 0
    command: ADD
    idle_timeout: 6
    hard_timeout: 0
    priority: 100
    buffer_id: NO_BUFFER
    flags: [ SEND_FLOW_REM ]
    match:
      - field: IPV4_SRC
        value: $match_ip_src
      - field: ETH_DST
        value: $match_eth_dst
      - field: TCP_DST
        value: $match_tcp_dst
    instructions:
      - instruction: APPLY_ACTIONS
        actions:
          - action: SET_FIELD
            field: ETH_SRC
            value: $eth_new_src
          - action: SET_FIELD
            field: IPV4_SRC
            value: $ip_new_src
          - action: OUTPUT
            port_no: $out_port
            max_len: MAX
''')

PACKET_OUT = zof.compile('''
  type: PACKET_OUT
  msg:
    actions:
      - action: OUTPUT
        port_no: $out_port
        max_len: MAX
    data: $data
''')

PACKET_FLOOD = zof.compile('''
  type: PACKET_OUT
  msg:
    in_port: $in_port
    actions:
      - action: OUTPUT
        port_no: FLOOD
        max_len: MAX
    data: $data
''')

if __name__ == '__main__':
    zof.run()

