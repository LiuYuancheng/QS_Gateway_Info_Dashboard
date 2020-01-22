import os
import time
import random
import pyshark
import itertools
from pyshark.packet.layer import JsonLayer
import logging
import ipaddress

import ciphersuite_parser

class ZeroPacketError(Exception):
    def __init__(self, message):
        super().__init__(message)

def searchEnums(rootdir, limit):
    """
    Given a root directory containing all the pcap files, it will search for all possible enums
    and return a list of all enums

    Set a hard limit on the number of files iterated through to save time
    """
    compressionmethods = []
    supportedgroups = []
    sighashalgorithms_client = []
    sighashalgorithms_cert = []

    success = 0
    failed = 0
    logging.info("Traversing through directory to find all enums...")
    files = os.listdir(rootdir)
    random.seed(2019)
    sampled_files = random.sample(files, min(len(files), limit))
    pkt_limit = 500

    for f in sampled_files:
        if f.endswith(".pcap"):

            pcapfile_capture = pyshark.FileCapture(os.path.join(rootdir,f))
            packets = []
            try:
                for i in range(pkt_limit):
                    packets.append(pcapfile_capture[i])
            except KeyError:
                pass
            pcapfile_capture.close()

            try:
                logging.info("Processing {}".format(f))
                starttime_traffic = time.time()
                found_clienthello = False # Variable for ending the packet loop if ClientHello is found
                found_certificate = False # Variable for ending the packet loop if Certificate is found

                for packet in packets:
                    starttime_packet = time.time()
                    # Compression Methods
                    traffic_compressionmethods = extractClienthelloCompressionmethod(packet)
                    compressionmethods.extend(traffic_compressionmethods)
                    # Supported Groups
                    traffic_supportedgroups = extractClienthelloSupportedgroup(packet)
                    supportedgroups.extend(traffic_supportedgroups)
                    # Clienthello - Signature Hash Algorithm
                    traffic_sighashalgorithms_client = extractClienthelloSignaturehash(packet)
                    sighashalgorithms_client.extend(traffic_sighashalgorithms_client)

                    if traffic_compressionmethods or traffic_sighashalgorithms_client:
                        found_clienthello = True

                    # Certificate - Signature Hash Algorithm
                    traffic_sighashalgorithms_cert = extractCertificate(packet)
                    sighashalgorithms_cert.extend(traffic_sighashalgorithms_cert)

                    if traffic_sighashalgorithms_cert:
                        found_certificate = True

                    logging.debug("Time spent on packet: {}s".format(time.time()-starttime_packet))

                    # Break the loop once both ClientHello and Certificate are found
                    if found_clienthello and found_certificate:
                        break

                logging.debug("Time spent on traffic: {}s".format(time.time()-starttime_traffic))

                # If ClientHello cannot be found in the traffic
                if not found_clienthello:
                    logging.warning("No ClientHello found for file {}".format(os.path.join(rootdir,f)))
                if not found_certificate:
                    logging.warning("No Certificate found for file {}".format(os.path.join(rootdir,f)))

                compressionmethods = list(set(compressionmethods))
                supportedgroups = list(set(supportedgroups))
                sighashalgorithms_client = list(set(sighashalgorithms_client))
                sighashalgorithms_cert = list(set(sighashalgorithms_cert))

                success += 1

            # Skip this pcap file
            except (KeyError, AttributeError, TypeError):
                logging.exception('Known error in file {}. Traffic is skipped'.format(f))
                failed+=1

            except Exception:
                logging.exception('Unknown error in file {}. Traffic is skipped')
                failed += 1

    logging.info("Done processing enum")
    print("Processed enums in directory {}: {} success, {} failure".format(rootdir,success, failed))

    enum = {}
    enum['compressionmethods'] = compressionmethods
    enum['supportedgroups'] = supportedgroups
    enum['sighashalgorithms_client'] = sighashalgorithms_client
    enum['sighashalgorithms_cert'] = sighashalgorithms_cert
    return enum

def extract_tcp_features(pcapfile, limit):

    # Traffic features for storing features of packets
    traffic_features = []
    traffic_appdata_segments_data = []

    pcapfile_capture = pyshark.FileCapture(pcapfile)
    packets = []
    try:
        for i in range(limit):
            packets.append(pcapfile_capture[i])
    except KeyError:
        pass
    pcapfile_capture.close()

    for packet in packets:

        packet_features = []

        # 1: COME/LEAVE
        comeLeaveFeature = extractComeLeaveFromPacket(packet)
        packet_features.extend(comeLeaveFeature)

        # 2: PROTOCOL
        protocolFeature = extractProtocolFromPacket(packet)
        packet_features.extend(protocolFeature)

        # 3: PACKET LENGTH
        lengthFeature = extractLengthFromPacket(packet)
        packet_features.extend(lengthFeature)

        # 4: INTERVAL
        intervalFeature = extractIntervalFromPacket(packet)
        packet_features.extend(intervalFeature)

        # 5: FLAG
        flagFeature = extractFlagFromPacket(packet)
        packet_features.extend(flagFeature)

        # 6: WINDOW SIZE
        windowSizeFeature = extractWindowSizeFromPacket(packet)
        packet_features.extend(windowSizeFeature)

        traffic_features.append(packet_features)

        packet_appdata_segments_idx = findIdxOfAppDataSegments(packet)
        if packet_appdata_segments_idx:
            traffic_appdata_segments_data.append((packet_appdata_segments_idx, protocolFeature))

    prot_start_idx = 1
    num_prot = 6
    for idx_list, flag in traffic_appdata_segments_data:
        for idx in idx_list:
            traffic_features[idx][prot_start_idx:prot_start_idx + num_prot] = flag

    if len(traffic_features) == 0:
        raise ZeroPacketError('Pcap file contains no packet')

    return traffic_features

def extractComeLeaveFromPacket(packet):
    feature = []
    if ipaddress.ip_address(str(packet.ip.dst)).is_private:
        feature.append(1)
    else:
        feature.append(0)

    return feature

def extractProtocolFromPacket(packet):
    # Protocol version value to encode into one-hot vector
    # prot: ['TCP' (-), 'SSL2.0' (0x0200), 'SSL3.0' (0x0300), 'TLS1.0' (0x0301), 'TLS1.1' (0x0302), 'TLS1.2' (0x0303)]
    protcol_ver = [0, 512, 768, 769, 770, 771]
    feature = [0] * len(protcol_ver)
    try:
        if hasattr(packet, 'ssl'):
            protocol = int(packet.ssl.record_version.show, 16)
            protocol_id = protcol_ver.index(protocol)
            feature[protocol_id] = 1
        elif hasattr(packet, 'tcp'):
            feature[0] = 1

    except ValueError:
        logging.warning('Found SSL packet with unknown SSL type {}'.format(protocol))

    except AttributeError:
        pass

    return feature

def extractLengthFromPacket(packet):
    return [int(packet.length)]

def extractIntervalFromPacket(packet):
    return [float(packet.frame_info.time_delta) * 1000]

def extractFlagFromPacket(packet):
    num_of_flags = 9
    try:
        # Convert hex into binary and pad left with 0 to fill 9 flags
        feature = list(bin(int(packet.tcp.flags, 16))[2:].zfill(num_of_flags))
        feature = list(map(int, feature))

    except AttributeError:
        feature = [0] * num_of_flags

    return feature

def extractWindowSizeFromPacket(packet):
    try:
        # Window size = window size value * scaling factor
        feature = [int(packet.tcp.window_size)]

    except AttributeError:
        feature = [0]

    return feature

def extract_tslssl_features(pcapfile, enums, limit):
    enumCompressionMethods = enums['compressionmethods']
    enumSupportedGroups = enums['supportedgroups']
    enumSignatureHashClient = enums['sighashalgorithms_client']
    enumSignatureHashCert = enums['sighashalgorithms_cert']

    # Traffic features for storing features of packets
    traffic_features = []
    traffic_appdata_segments_idx = []

    pcapfile_capture = pyshark.FileCapture(pcapfile)
    packets = []
    try:
        for i in range(limit):
            packets.append(pcapfile_capture[i])
    except KeyError:
        pass
    pcapfile_capture.close()

    for packet in packets:

        packet_features = []

        # HANDSHAKE PROTOCOL
        ##################################################################
        # 1: ClientHello - LENGTH
        clienthelloLengthFeature = extractClienthelloLength(packet)
        packet_features.extend(clienthelloLengthFeature)

        # 2: ClientHello - CIPHER SUITE
        clienthelloCiphersuiteFeature = extractClienthelloCiphersuite(packet)
        packet_features.extend(clienthelloCiphersuiteFeature)

        # 3: ClientHello - CIPHER SUITE LENGTH
        clienthelloCiphersuiteLengthFeature = extractClienthelloCiphersuiteLength(packet)
        packet_features.extend(clienthelloCiphersuiteLengthFeature)

        # 4: ClientHello - COMPRESSION METHOD
        clienthelloCompressionMethodFeature = extractClienthelloCompressionmethodAndEncode(packet,
                                                                                           enumCompressionMethods)
        packet_features.extend(clienthelloCompressionMethodFeature)

        # 5: ClientHello - SUPPORTED GROUP LENGTH
        clienthelloSupportedgroupLengthFeature = extractClienthelloSupportedgroupLength(packet)
        packet_features.extend(clienthelloSupportedgroupLengthFeature)

        # 6: ClientHello - SUPPORTED GROUPS
        clienthelloSupportedgroupFeature = extractClienthelloSupportedgroupAndEncode(packet, enumSupportedGroups)
        packet_features.extend(clienthelloSupportedgroupFeature)

        # 7: ClientHello - ENCRYPT THEN MAC LENGTH
        clienthelloEncryptthenmacLengthFeature = extractClienthelloEncryptthenmacLength(packet)
        packet_features.extend(clienthelloEncryptthenmacLengthFeature)

        # 8: ClientHello - EXTENDED MASTER SECRET
        clienthelloExtendedmastersecretLengthFeature = extractClienthelloExtendedmastersecretLength(packet)
        packet_features.extend(clienthelloExtendedmastersecretLengthFeature)

        # 9: ClientHello - SIGNATURE HASH ALGORITHM
        clienthelloSignaturehashFeature = extractClienthelloSignaturehashAndEncode(packet, enumSignatureHashClient)
        packet_features.extend(clienthelloSignaturehashFeature)

        # 10: ServerHello - LENGTH
        serverhelloLengthFeature = extractServerhelloLength(packet)
        packet_features.extend(serverhelloLengthFeature)

        # 11: ServerHello - EXTENDED MASTER SECRET
        # Feature cannot be found in the packet

        # 12: ServerHello - RENEGOTIATION INFO LENGTH
        serverhelloRenegoLengthFeature = extractServerhelloRenegoLength(packet)
        packet_features.extend(serverhelloRenegoLengthFeature)

        # 13,14,15,16: Certificate - NUM_CERT, AVERAGE, MIN, MAX CERTIFICATE LENGTH
        certificateLengthInfoFeature = extractCertificateLengthInfo(packet)
        packet_features.extend(certificateLengthInfoFeature)

        # 17: Certificate - SIGNATURE ALGORITHM
        certificateFeature = extractCertificateAndEncode(packet, enumSignatureHashCert)
        packet_features.extend(certificateFeature)

        # 18: ServerHelloDone - LENGTH
        serverhellodoneLengthFeature = extractServerhellodoneLength(packet)
        packet_features.extend(serverhellodoneLengthFeature)

        # 19: ClientKeyExchange - LENGTH
        clientkeyexchangeLengthFeature = extractClientkeyexchangeLength(packet)
        packet_features.extend(clientkeyexchangeLengthFeature)

        # 20: ClientKeyExchange - PUBKEY LENGTH
        clientkeyexchangePubkeyLengthFeature = extractClientkeyexchangePubkeyLength(packet)
        packet_features.extend(clientkeyexchangePubkeyLengthFeature)

        # 21: EncryptedHandshakeMessage - LENGTH
        encryptedhandshakemsgLengthFeature = extractEncryptedhandshakemsgLength(packet)
        packet_features.extend(encryptedhandshakemsgLengthFeature)

        #  CHANGE CIPHER PROTOCOL
        ##################################################################
        # 22: ChangeCipherSpec - LENGTH
        changecipherspecLengthFeature = extractChangeCipherSpecLength(packet)
        packet_features.extend(changecipherspecLengthFeature)

        #  APPLICATION DATA PROTOCOL
        ##################################################################
        # 23: ApplicationDataProtocol - LENGTH
        # Set app data length for pure app data packets first, modify app data length for TCP segments
        # for reassembled PDU later
        appdataLengthFeature = extractAppDataLength(packet)
        packet_features.extend(appdataLengthFeature)

        # Finding all index of TCP segments for reassembed PDU
        packet_appdata_segments_idx = findIdxOfAppDataSegments(packet)
        traffic_appdata_segments_idx.extend(packet_appdata_segments_idx)

        # Convert to float for standardization
        packet_features = [float(i) for i in packet_features]
        traffic_features.append(packet_features)

    traffic_appdata_segments_idx = list(set(traffic_appdata_segments_idx)) # Remove duplicates from the list first
    for idx in traffic_appdata_segments_idx:
        try:
            # Use tcp.len as the application data length
            traffic_features[idx][-1] = float(packets[idx].tcp.len)
        except AttributeError:
            pass

    if len(traffic_features) == 0:
        raise ZeroPacketError('Pcap file contains no packet')

    return traffic_features

def extractClienthelloLength(packet):
    feature = [0]
    try:
        clienthello_type = '1'
        handshake_type = [field.show for field in packet.ssl.handshake_type.all_fields]
        handshake_len = [field.show for field in packet.ssl.handshake_length.all_fields]
        clienthello_idx = handshake_type.index(clienthello_type)
        feature = [int(handshake_len[clienthello_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

def extractClienthelloCiphersuite(packet):
    feature_len = sum(map(len, [getattr(ciphersuite_parser, component) for component in ciphersuite_parser.components]))
    feature = [0] * feature_len
    try:
        if int(packet.ssl.handshake_type)==1:
            raw_fields = [field.show for field in packet.ssl.handshake_ciphersuite.all_fields]
            dec_ciphersuites = [int(field) for field in raw_fields]
            feature = ciphersuite_parser.getVecAndAggregateAndNormalize(dec_ciphersuites)

    except (AttributeError, ZeroDivisionError):
        pass

    return feature

def extractClienthelloCiphersuiteLength(packet):
    feature = [0]
    try:
        feature = [int(packet.ssl.handshake_cipher_suites_length)]

    except AttributeError:
        pass

    return feature

def extractClienthelloCompressionmethodAndEncode(packet, enum):
    compressionmethods = extractClienthelloCompressionmethod(packet)
    encoded_compressionmethods = encodeEnumIntoManyHotVec(compressionmethods, enum)
    if encoded_compressionmethods[-1] == 1:
        logging.warning('Compression methods contain unseen enums. Refer to above')

    return encoded_compressionmethods

def extractClienthelloCompressionmethod(packet):
    feature = []
    try:
        if int(packet.ssl.handshake_type)==1:
            raw_fields = [field.show for field in packet.ssl.handshake_comp_method.all_fields]
            feature = [int(field, 16) for field in raw_fields]

    except AttributeError:
        pass

    return feature

def extractClienthelloSupportedgroupLength(packet):
    feature = [0]
    try:
        feature = [int(packet.ssl.handshake_extensions_supported_groups_length)]

    except AttributeError:
        pass

    return feature

def extractClienthelloSupportedgroupAndEncode(packet, enum):
    supportedgroups = extractClienthelloSupportedgroup(packet)
    encoded_supportedgroups = encodeEnumIntoManyHotVec(supportedgroups, enum)
    if encoded_supportedgroups[-1] == 1:
        logging.warning('Supported groups contain unseen enums. Refer to above')

    return encoded_supportedgroups

def extractClienthelloSupportedgroup(packet):
    feature = []
    try:
        raw_fields = [field.show for field in packet.ssl.handshake_extensions_supported_group.all_fields]
        feature = [int(field, 16) for field in raw_fields]

    except AttributeError:
        pass

    return feature

def extractClienthelloEncryptthenmacLength(packet):
    feature = [0]
    try:
        encryptthenmac_type = '22'
        handshake_extension_type = [field.show for field in packet.ssl.handshake_extension_type.all_fields]
        handshake_extension_len = [field.show for field in packet.ssl.handshake_extension_len.all_fields]
        encryptthenmac_idx = handshake_extension_type.index(encryptthenmac_type)
        feature = [int(handshake_extension_len[encryptthenmac_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

def extractClienthelloExtendedmastersecretLength(packet):
    feature = [0]
    try:
        extendedmastersecret_type = '23'
        handshake_extension_type = [field.show for field in packet.ssl.handshake_extension_type.all_fields]
        handshake_extension_len = [field.show for field in packet.ssl.handshake_extension_len.all_fields]
        extendedmastersecret_idx = handshake_extension_type.index(extendedmastersecret_type)
        feature = [int(handshake_extension_len[extendedmastersecret_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

def extractClienthelloSignaturehashAndEncode(packet, enum):
    signaturehashes = extractClienthelloSignaturehash(packet)
    encoded_signaturehashes = encodeEnumIntoManyHotVec(signaturehashes, enum)
    if encoded_signaturehashes[-1] == 1:
        logging.warning('Signature hash contains unseen enums. Refer to above')

    return encoded_signaturehashes

def extractClienthelloSignaturehash(packet):
    feature = []
    try:
        if int(packet.ssl.handshake_type)==1:
            raw_fields = [field.show for field in packet.ssl.handshake_sig_hash_alg.all_fields]
            feature = [int(field, 16) for field in raw_fields]

    except AttributeError:
        pass

    return feature

def extractServerhelloLength(packet):
    feature = [0]
    try:
        serverhello_type = '2'
        handshake_type = [field.show for field in packet.ssl.handshake_type.all_fields]
        handshake_len = [field.show for field in packet.ssl.handshake_length.all_fields]
        serverhello_idx = handshake_type.index(serverhello_type)
        feature = [int(handshake_len[serverhello_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

def extractServerhelloRenegoLength(packet):
    feature = [0]
    try:
        feature = [int(packet.ssl.handshake_extensions_reneg_info_len)]

    except AttributeError:
        pass

    return feature

def extractCertificateLengthInfo(packet):
    feature = [0,0,0,0]
    try:
        raw_fields = [field.show for field in packet.ssl.handshake_certificate_length.all_fields]
        cert_len = [int(field) for field in raw_fields]
        num_cert = len(cert_len)
        mean_cert_len = sum(cert_len) / float(num_cert)
        max_cert_len = max(cert_len)
        min_cert_len = min(cert_len)
        feature = [num_cert, mean_cert_len, max_cert_len, min_cert_len]

    except AttributeError:
        pass

    return feature

def extractCertificateAndEncode(packet, enum):
    certs = extractCertificate(packet)
    encoded_certs = encodeEnumIntoManyHotVec(certs, enum)
    if encoded_certs[-1] == 1:
        logging.warning('Certificates contains unseen enums. Refer to above')

    return encoded_certs

def extractCertificate(packet):
    feature = []
    try:
        # Need to scan through layers attribute instead of access ssl attribute directly
        # because pyshark cant extract inner attributes for duplicate ssl layers
        raw_fields = []
        for layer in packet.layers:
            if layer.layer_name == 'ssl' and hasattr(layer, 'x509af_algorithm_id'):
                raw_fields.extend([field.show for field in layer.x509af_algorithm_id.all_fields])
        feature = [str(field) for field in set(raw_fields)]

    except AttributeError:
        pass

    return feature

def extractServerhellodoneLength(packet):
    feature = [0]
    try:
        serverhellodone_type = '14'
        handshake_type = []
        handshake_len = []
        # Need to scan through layers attribute instead of accessing ssl attribute directly
        # because pyshark cant extract inner attributes for duplicate ssl layers
        for layer in packet.layers:
            if layer.layer_name == 'ssl' and hasattr(layer, 'handshake_type') and hasattr(layer, 'handshake_length'):
                handshake_type.extend([field.show for field in layer.handshake_type.all_fields])
                handshake_len.extend([field.show for field in layer.handshake_length.all_fields])
        serverhellodone_idx = handshake_type.index(serverhellodone_type)
        feature = [int(handshake_len[serverhellodone_idx])]

    except (AttributeError,ValueError):
        pass

    return feature

def extractClientkeyexchangeLength(packet):
    feature = [0]
    try:
        clientkeyexchange_type = '16'
        handshake_type = [field.show for field in packet.ssl.handshake_type.all_fields]
        handshake_len = [field.show for field in packet.ssl.handshake_length.all_fields]
        clientkeyexchange_idx = handshake_type.index(clientkeyexchange_type)
        feature = [int(handshake_len[clientkeyexchange_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

def extractClientkeyexchangePubkeyLength(packet):
    feature = [0]
    try:
        feature = [int(packet.ssl.handshake_client_point_len)]

    except AttributeError:
        pass

    return feature

def extractEncryptedhandshakemsgLength(packet):
    feature = [0]
    try:
        encryptedhandshakemsg_record_name = 'Encrypted Handshake Message'
        record_names = [field.showname for field in packet.ssl.record.all_fields]
        record_lengths = [field.show for field in packet.ssl.record_length.all_fields]
        in_record_names = [encryptedhandshakemsg_record_name in record_name for record_name in record_names]
        tmp = [int(record_length) for i, record_length in enumerate(record_lengths) if in_record_names[i] == True]
        if tmp:
            feature = [sum(tmp)]

    except AttributeError:
        pass

    return feature

def extractChangeCipherSpecLength(packet):
    feature = [0]
    try:
        changecipherspec_type = '20'
        record_type = [field.show for field in packet.ssl.record_content_type.all_fields]
        record_len = [field.show for field in packet.ssl.record_length.all_fields]
        changecipherspec_idx = record_type.index(changecipherspec_type)
        feature = [int(record_len[changecipherspec_idx])]

    except (AttributeError, ValueError):
        pass

    return feature

# If there are more than 1 app data record layer in the same packet, it will extract the latest app data record layer
def extractAppDataLength(packet):
    feature = [0]
    try:
        # Check if it is an application data packet and extract the len of tcp payload only
        appdata_type = '23'
        record_type = [field.show for field in packet.ssl.record_content_type.all_fields]
        if appdata_type in record_type:
            feature = [int(packet.tcp.len)]

    except AttributeError:
        pass

    return feature

def findIdxOfAppDataSegments(packet):
    appdata_segments_idx = []
    try:
        # Verify that it is a app data ssl packet and
        # that it has a data layer containing info about reassembled tcp pkt
        if hasattr(packet, 'ssl') and hasattr(packet.ssl, 'app_data') and hasattr(packet, 'data'):
            raw_fields = [field.show for field in packet.data.tcp_segment.all_fields]
            appdata_segments_idx.extend(list(map(lambda x:int(str(x))-1, raw_fields)))

    except (AttributeError, KeyError):
        pass

    return appdata_segments_idx

def find_handshake(obj, target_type):
    if type(obj) == list:
        final = None
        for a_obj in obj:
            temp = find_handshake(a_obj, target_type)
            if temp:
                final = temp
        return final

    elif type(obj) == JsonLayer:
        if obj.layer_name=='ssl' and hasattr(obj, 'record'):
            return find_handshake(obj.record, target_type)
        # elif obj.layer_name=='ssl' and hasattr(obj, 'handshake'):
        #     return find_handshake(obj.handshake, target_type)
        elif obj.layer_name=='record' and hasattr(obj, 'handshake') and target_type!=99:
            return find_handshake(obj.handshake, target_type)
        # If correct handshake is identified
        elif obj.layer_name=='handshake' and int(obj.type)==target_type:
            return obj
        # Return record containing Encrypted Handshake Message (only handshake msg without a type)
        elif obj.layer_name=='record' and hasattr(obj, 'handshake') and not(type(obj.handshake)==JsonLayer) and target_type==99:
            return obj

    elif type(obj) == dict:
        if 'ssl.record' in obj:
            return find_handshake(obj['ssl.record'], target_type)
        elif 'ssl.handshake' in obj:
            return find_handshake(obj['ssl.handshake'], target_type)
        elif 'ssl.handshake.type' in obj and int(obj['ssl.handshake.type'])==target_type:
            return obj

def find_changecipher(obj):
    if type(obj) == list:
        final = None
        for a_obj in obj:
            temp = find_changecipher(a_obj)
            if temp:
                final = temp
        return final

    elif type(obj)==JsonLayer:
        if obj.layer_name=='ssl' and hasattr(obj, 'record'):
            return find_changecipher(obj.record)
        elif obj.layer_name=='record' and hasattr(obj, 'change_cipher_spec'):
            return obj

# For identifying pure Application Data and Application Data [TCP segment of a reassembled PDU]
def find_appdata(obj, appdata):
    if type(obj) == list:
        for a_obj in obj:
            find_appdata(a_obj, appdata)

    elif type(obj)==JsonLayer:
        if obj.layer_name=='ssl' and hasattr(obj, 'record'):
            find_appdata(obj.record, appdata)
        elif obj.layer_name=='record' and hasattr(obj, 'app_data'):
            appdata.append(obj)

    elif type(obj) == dict:
        if 'ssl.record' in obj:
            find_appdata(obj['ssl.record'], appdata)
        elif 'ssl.app_data' in obj:
            appdata.append(obj)

def encodeEnumIntoManyHotVec(listOfEnum, refEnum):
    unknown_dim = [0]
    # The unknown dim occupies the last position
    encoded_enums = [0] * len(refEnum) + unknown_dim
    if listOfEnum:
        for enum in listOfEnum:
            if enum in refEnum:
                encoded_enums[refEnum.index(enum)] = 1
            else:
                encoded_enums[-1] = 1
                logging.warning('Unseen enum {}'.format(enum))
    return encoded_enums

if __name__ == '__main__':
    enums = {'ciphersuites': [], 'compressionmethods': [], 'supportedgroups': [], 'sighashalgorithms_client': [],
             'sighashalgorithms_cert': []}

    # Find attributes of a packet in pyshark.FileCapture
    pcapfile = 'sample-pcap/tls/www.stripes.com_2018-12-21_16-20-12.pcap'
    packets = pyshark.FileCapture(pcapfile)
    packets_list = [packet for packet in packets]
    clienthello = packets_list[3]
    supportedgroups = clienthello.ssl.handshake_extensions_supported_group
    for i in supportedgroups.all_fields:
        print(dir(i))
        print(i.show)
        print(i.showname)
        print(i.showname_key)
        print(i.showname_value)
        print(i.hex_value)

