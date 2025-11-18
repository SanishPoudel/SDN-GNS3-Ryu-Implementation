# blocks all pings
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3

class BlockPingAll(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(BlockPingAll, self).__init__(*args, **kwargs)
        self.datapaths = {}

    @set_ev_cls(ofp_event.EventOFPStateChange, MAIN_DISPATCHER)
    def state_change_handler(self, ev):
        dp = ev.datapath
        self.datapaths[dp.id] = dp
        self._block_ping(dp)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        self._block_ping(dp)

    def _add_flow(self, dp, match, actions, priority=10):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp,
                                priority=priority,
                                match=match,
                                instructions=inst)
        dp.send_msg(mod)

    def _block_ping(self, dp):
        parser = dp.ofproto_parser
        ofproto = dp.ofproto

        # Drop ICMP echo request
        match_ping = parser.OFPMatch(eth_type=0x0800, ip_proto=1, icmpv4_type=8)
        self._add_flow(dp, match_ping, [], priority=20)

        # Allow all other traffic
        match_all = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self._add_flow(dp, match_all, actions, priority=0)
