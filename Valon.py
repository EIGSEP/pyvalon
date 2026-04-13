
import serial
import time
import struct
import math

RECV_LEN = 1024

class Valon(object):
    """
    Description:
        This class is defined for all the valon devices,
        which uses serial port.
    """
    def __init__(self, dev, baud):
        self.ser = serial.Serial(dev,baud,timeout=0.5, rtscts=False, xonxoff=False)
    
    def sendcmd(self, cmd):
        try:
            self.ser.write(cmd.encode('utf-8'))
            r = self.ser.read(RECV_LEN).decode()
        except:
            self.ser.write(cmd)
            r = self.ser.read(RECV_LEN)
        return r

    def close(self):
        self.ser.close()

class V5015(Valon):
    """
    Description:
        This class is based on Valon class, 
        and is especially for V5015
    """
    def SetFreq(self, f=-1, u='MHz', verbose=False):
        """
        Set Frequency.

        Inputs:
            - f (float): the freqency value.
            - u (str): freqency unit, such as "MHz".
            - verbose (bool): be verbose
                Default=False
        Ouputs:
            - r (str): the frequency been set
        """
        if f == -1:
            cmd = 'F\r'
        else:
            if u == 'MHz' and f > 15000:
                f = 15000
                print('The max freq is 15000MHz.')
            elif u == 'GHz' and f > 15:
                f = 15
                print('The max freq is 15GHz.')
            cmd = 'F ' + str(f) + ' ' + u + '\r'
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        if f == -1:
            rs = r.split(';')[0].split(' ')
        else:
            rs = r.split('\r')[0].split(' ')
        return rs[1]+rs[2]
    
    def SetAmp(self, a=100, verbose=False):
        """
        Set Amplitude in dBm.

        Inputs:
            - a (float): amplitude in dBm.
            - verbose (bool): be verbose
                Default=False
        Ouputs:
            - r (str): the amplitude been set
        """
        if a == 100:
            cmd = 'PWR\r'
        else:
            if a > 14:
                a = 14
                print('The max amplitude is 14dBm.')
            cmd = 'PWR ' + str(a) + '\r' 
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        
        rs0 = r.split(';')[0].split(' ')
        rs1 = r.split(';')[1].split(' ')[3].split('\r')
        if a == 100:
            return rs0[1]+rs1[0]
        else:
            return rs0[2]+rs1[0]
        
    
    def SetRef(self, s='', f=10, verbose=False):
        """
        Set Ref and Ref source in MHz 

        Inputs:
            - s (str): reference source('internal' or 'external'). 
                Default=''
            - f (int): reference frequency in MHz. It should be in the ref_list.
                Default=10
            - verbose (bool): be verbose
                Default=False
        Outputs:
            - r (str): ref source and ref frequency in MHz
        """
        if s == 'internal':
            src = str(0)
        elif s == 'external':
            src = str(1)
        else:
            src = ''
        # set refernce source first
        cmd = 'REFS ' + src + '\r'
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        rs = r.split(';')[0].split(' ')
        ref_src=''
        if rs[2] == '0':
            ref_src += 'internal'
        elif rs[2] == '1':
            ref_src += 'external'
        # ser reference frequency in MHz
        cmd = 'REF ' + str(f) + ' ' + 'MHz\r'
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        rs1 = r.split(';')[0].split(' ')
        rs2 = r.split(';')[0].split(' ')[2].split('\r')
        ref_val = rs1[1] + rs2[0]
        return ref_src + ' ' + ref_val
    
    def RFout(self, s='', verbose=False):
        """
        Turn on/off the RFout.

        Inputs:
            - s (str): RFout status('on' or 'off')
            - verbose (bool): be verbose
                Default=False
        Outputs:
            - r (str): RFout status
        """
        if len(s) == 0:
            cmd = 'OEN\r'
            index = 1
        else:
            cmd = 'OEN ' + s.upper() + '\r'
            index = 2
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        rs = r.split(';')[0].split(' ')
        if rs[index] == '0':
            return 'OFF'
        elif rs[index] == '1':
            return 'ON'
    
    def PWRout(self, s='', verbose=False):
        """
        Power on/off the synth.

        Inputs:
            - s(str): Power status('on' or 'off')
            - verbose (bool): be verbose
                Default=False
        Ouputs:
            - r(str): Power status
        """
        if len(s) == 0:
            cmd = 'PDN\r'
            index = 1
        else:
           cmd = 'PDN ' + s.upper() + '\r' 
           index = 2
        r = self.sendcmd(cmd)
        if verbose:
            print(r)
        rs = r.split(';')[0].split(' ')
        if rs[index] == '0':
            return 'OFF'
        elif rs[index] == '1':
            return 'ON'

      
class V500X(object):
    """
    Description:
        This class is based on Valon class, 
        and is especially for V5007 and V5008.
    """
    SYNTH = {
        'A': 0x00,
        'B': 0x08
    }  
    REPLY = {
        'ACK': 0x06,
        'NACK': 0x15
    }
    def __init__(self, dev, baud=9600):
        self.ser = serial.Serial(dev,baud,timeout=0.5, rtscts=False, xonxoff=False)
    
    def _write(self, cmd):
        self.ser.write(cmd)
    
    def _read(self, l):
        return self.ser.read(l)
    
    def close(self):
        self.ser.close()

    def _pack_int(self, val, d, offset):
        r = struct.pack('>i', val)
        d[offset:offset+4] = r

    def _unpack_int(self, d, offset):
        r = struct.unpack('>i', d[offset:offset+4])[0]
        return r

    def _pack_short(self, val, d, offset):
        r = struct.pack('>h', val)
        d[offset:offset+2] = r

    def _unpack_short(self, d, offset):
        r = struct.unpack('>h', d[offset:offset+2])[0]
        return r

    def _generate_checksum(self, d):
        """
        Description:
            Generate checksum.
        Inputs:
            - d (bytes): 
                data.
        Outputs:
            - c (byte):
                checksum
        """
        sum = 0;
        for i in range(len(d)):
            sum = sum + d[i]
        return sum & 0xff

    def _verify_checksum(self, data, checksum):
        cs = checksum[0] if isinstance(checksum, (bytes, bytearray)) else checksum
        return self._generate_checksum(data) == cs

    def CheckReadBack(self, b, l, c):
        """
        Description:
            Check the read back data - 1: the data length; 2 - checksum.
        Inputs:
            b (bytearray): the read back data
            l (int): the expected data length
            c (byte): the expected checksum value 
        """
        if len(b) != l or len(c) != 1:
            print("Read Back data incorrect: The length should be %d, while it's %d"%(l, len(b)))
            return False
        if not self._verify_checksum(b, c):
            print('Checksum is incorrect.')
            return False
        return True

    def _pack_freq_registers(self, regs, d, offset):
        dbf = int(math.log2(regs['dbf']))
        reg0 = self._unpack_int(d, 0+offset)
        reg1 = self._unpack_int(d, 4+offset)
        reg4 = self._unpack_int(d, 16+offset)
        reg0 &= 0x80000007
        reg0 |= ((regs['ncount'] & 0xffff) << 15) | ((regs['frac'] & 0x0fff) << 3)
        reg1 &= 0xffff8007
        reg1 |= (regs['mod'] & 0x0fff) << 3
        reg4 &= 0xff8fffff
        reg4 |= dbf << 20
        self._pack_int(reg0, d, 0+offset)
        self._pack_int(reg1, d, 4+offset)
        self._pack_int(reg4, d, 16+offset)  

    def _unpack_freq_registers(self, d):
        reg0 = self._unpack_int(d, 0)
        reg1 = self._unpack_int(d, 4)
        reg4 = self._unpack_int(d, 16)
        regs = {}
        regs['ncount'] = (reg0 >> 15) & 0xffff
        regs['frac'] = (reg0 >> 3) & 0x0fff
        regs['mod'] = (reg1 >> 3) & 0x0fff
        dbf = (reg4 >> 20) & 0x07
        if dbf >=0 and dbf <= 4:
            regs['dbf'] = 2**dbf
        else:
            regs['dbf'] = 1
        return regs

    def GetReference(self):
        """
        Description:
            Get the reference frequency
        Outputs:
            freq (float): reference frequency in Hz
        """
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x81
        self._write(cmdbytes)
        b = self._read(4)
        c = self._read(1)
        if self.CheckReadBack(b,4,c) == False:
            return
        freq = self._unpack_int(b, 0)
        return freq
    
    def SetReference(self, freq):
        """
        Description:
            Set the reference frequency.
        Inputs:
            - freq (int): reference frequency in Hz.
        Outputs:
            - success (bool): True if ACK received.
        """
        data = struct.pack('>BI', 0x01, freq)
        cs = self._generate_checksum(data)
        self._write(data + bytes([cs]))
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def GetOptions(self, synth):
        """
        Description:
            This is used for getting the synthesizer's configuration.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outputs:
            - opts (dict): synthesizer's configuration.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x80|s
        self._write(cmdbytes)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b, 24, c) == False:
            return
        reg2 = self._unpack_int(b, 8)
        opts = {}
        opts['low_spur'] = ((reg2 >> 30) & 1) & ((reg2 >> 29) & 1);
        opts['double_ref'] = (reg2 >> 25) & 1;
        opts['half_ref'] = (reg2 >> 24) & 1;
        opts['r'] = (reg2 >> 14) & 0x03ff;
        return opts

    def SetOptions(self, synth, double=0, half=0, divider=1, low_spur=0):
        """
        Description:
            Set the synthesizer's configuration options.
        Inputs:
            - synth (str): 'A' or 'B'.
            - double (int): 1 to double reference frequency, 0 otherwise.
            - half (int): 1 to halve reference frequency, 0 otherwise.
            - divider (int): reference frequency divisor (1-1023).
            - low_spur (int): 1 to minimize spurs, 0 to minimize phase noise.
        Outputs:
            - success (bool): True if ACK received.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return False
        # Read current registers
        cmdbyte = bytearray(1)
        cmdbyte[0] = 0x80 | s
        self._write(cmdbyte)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b, 24, c) == False:
            return False
        # Modify reg2
        reg2 = self._unpack_int(b, 8)
        reg2 &= 0x9c003fff
        reg2 |= (((low_spur & 1) << 30) | ((low_spur & 1) << 29) |
                 ((double & 1) << 25) | ((half & 1) << 24) |
                 ((divider & 0x03ff) << 14))
        # Write back
        cmdbytes = bytearray(26)
        cmdbytes[0] = 0x00 | s
        cmdbytes[1:25] = b
        self._pack_int(reg2, cmdbytes, 9)
        cmdbytes[25] = self._generate_checksum(cmdbytes[:25])
        self._write(cmdbytes)
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def GetEPDF(self, synth, verbose=False):
        """
        Description:
            This is used for the refernce calculation.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outputs:
            - reference (float): reference freq in MHz
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        reference = self.GetReference()
        opts = self.GetOptions(synth)
        if verbose:
            print('reference: ', reference)
            print('double_ref: ', opts['double_ref'])
            print('half_ref: ', opts['half_ref'])
            print('r: ', opts['r'])
        if opts['double_ref']:
            reference *= 2.0;
        if opts['half_ref']:
            reference /= 2.0;
        if opts['r'] > 1:
            reference /= opts['r'];
        if verbose:
            print('calculated reference: ', reference)
        return reference

    def GetVCORange(self, synth):
        """
        Description:
            Get the VCO range.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outputs:
            - vcor (dict): the vco range.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x83|s
        self._write(cmdbytes)
        b = self._read(4)
        c = self._read(1)
        if self.CheckReadBack(b,4,c) == False:
            return
        vcor = {}
        vcor['min'] = self._unpack_short(b,0)
        vcor['max'] = self._unpack_short(b,2)
        return vcor

    def SetVCORange(self, synth, low, high):
        """
        Description:
            Set the VCO range.
        Inputs:
            - synth (str): 'A' or 'B'.
            - low (int): minimum VCO frequency in MHz.
            - high (int): maximum VCO frequency in MHz.
        Outputs:
            - success (bool): True if ACK received.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return False
        data = struct.pack('>BHH', 0x03 | s, low, high)
        cs = self._generate_checksum(data)
        self._write(data + bytes([cs]))
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def GetLabel(self, synth):
        """
        Description:
            Get synthesizer label or name.
        Inputs:
            - synth (str): 'A' or 'B'.
        Outputs:
            - label (str): up to 16 characters.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x82 | s
        self._write(cmdbytes)
        b = self._read(16)
        c = self._read(1)
        if self.CheckReadBack(b, 16, c) == False:
            return
        return b.rstrip(b'\x00').decode('utf-8', errors='replace')

    def SetLabel(self, synth, label):
        """
        Description:
            Set synthesizer label or name.
        Inputs:
            - synth (str): 'A' or 'B'.
            - label (str): up to 16 characters.
        Outputs:
            - success (bool): True if ACK received.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return False
        if isinstance(label, str):
            label = label.encode('utf-8')
        label = label[:16].ljust(16, b'\x00')
        data = struct.pack('>B', 0x02 | s) + label
        cs = self._generate_checksum(data)
        self._write(data + bytes([cs]))
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def GetFreq(self, synth, verbose=False):
        """
        Description:
            Get the frequency.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outputs:
            - freq (float): The output frequency in MHz.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x80|s
        self._write(cmdbytes)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b,24,c) == False:
            return
        EPDF = self.GetEPDF(synth)
        regs = self._unpack_freq_registers(b)
        if verbose:
            print('EPDF: ', EPDF)
            print('dbf:', regs['dbf'])
            print('ncount:', regs['ncount'])
            print('frac:', regs['frac'])
            print('mod:', regs['mod'])
        try:
            freq =  (regs['ncount'] + float(regs['frac']) / regs['mod']) * EPDF / regs['dbf']
        except:
            print("The synthesizer seems not to be set.")
            return 0
        return freq        
            

    def SetFreq(self, synth, freq, chan_spacing = 0.01, verbose = False):
        """
        Description:
            Set the frequency.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
            - freq (float): the output frequency in MHz.
            - chan_spacing (float): the freqnency increment in MHz
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        dbf = 1
        vcor = self.GetVCORange(synth)
        while (freq * dbf) <= vcor['min'] and dbf <= 16:
            dbf *= 2
        if dbf > 16:
            dbf = 16
        vco = freq * dbf
        EPDF = self.GetEPDF(synth)
        regs = {}
        regs['ncount'] = int(vco/EPDF)
        regs['frac'] = int((vco - regs['ncount'] * EPDF) / chan_spacing + 0.5);
        regs['mod'] = int(EPDF / chan_spacing + 0.5);
        regs['dbf'] = dbf;
        # Reduce frac/mod to simplest fraction
        if regs['frac'] != 0 and regs['mod'] != 0:
            while (not (regs['frac'] &1 ) and (not (regs['mod'] &1))): 
                regs['frac'] = int(regs['frac']/2)
                regs['mod'] = int(regs['mod']/2)
        else:
            regs['frac'] = 0
            regs['mod'] = 1
        if verbose:
            print('EPDF: ', EPDF)
            print('dbf:', regs['dbf'])
            print('ncount:', regs['ncount'])
            print('frac:', regs['frac'])
            print('mod:', regs['mod'])
            
        #Write values to hardware
        cmdbyte = bytearray(1)
        cmdbyte[0] = 0x80|s
        self._write(cmdbyte)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b,24,c) == False:
            return
        cmdbytes = bytearray(26)
        cmdbytes[0] = 0x00|s
        cmdbytes[1:25] = b
        self._pack_freq_registers(regs, cmdbytes, 1)
        cmdbytes[25] = self._generate_checksum(cmdbytes[:25])
        self._write(cmdbytes)
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False
    
    def GetRFLevel(self, synth, verbose=False):
        """
        Description:
            Get the RF output level.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outputs:
            - rf_level (int): RF output level.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x80|s
        self._write(cmdbytes)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b,24,c) == False:
            return
        reg4 = self._unpack_int(b, 16)
        if verbose:
            print('raw reg data:', b)
            print('reg4:', hex(reg4))
        rfl = (reg4 >> 3) & 0x03
        if rfl == 0:
            rf_level = -4
        elif rfl == 1:
            rf_level = -1
        elif rfl == 2:
            rf_level = 2
        elif rfl == 3:
            rf_level = 5
        return rf_level 

    def SetRFLevel(self, synth, rf_level):
        """
        Description:
            Set the RF output level.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
            - rf_level (int): -4, -1, 2 or 5.
        """     
        if rf_level == -4:
            rfl = 0
        elif rf_level == -1:
            rfl = 1
        elif rf_level == 2:
            rfl = 2
        elif rf_level == 5:
            rfl = 3
        else:
            print('Invalid options.')
            print('The valid option is -4, -1, 2 or 5')
            return False
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbyte = bytearray(1)
        cmdbyte[0] = 0x80|s
        self._write(cmdbyte)
        b = self._read(24)
        c = self._read(1)
        if self.CheckReadBack(b,24,c) == False:
            return
        reg4 = self._unpack_int(b, 16)
        reg4 &= 0xffffffe7
        reg4 |= (rfl & 0x03) << 3
        cmdbytes = bytearray(26)
        cmdbytes[0] = 0x00|s
        cmdbytes[1:25] = b
        self._pack_int(reg4, cmdbytes, 17)
        cmdbytes[25] = self._generate_checksum(cmdbytes[:25])
        self._write(cmdbytes)
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def GetPhaseLock(self, synth, verbose=False):
        """
        Description:
            Check if the synthesizer is locked or not.
        Inputs:
            - synth (str): A - synthesizer 1; B - synthesizer 2.
        Outpus:
            - locked (bool): True - locked; False - unlocked.
        """
        try:
            s = V500X.SYNTH[synth]
        except:
            print('synth is not supported.')
            return
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x86|s
        self._write(cmdbytes)
        b = self._read(1)
        c = self._read(1)
        if self.CheckReadBack(b,1,c) == False:
            return
        if synth == 'A':
            mask = 0x20
        elif synth == 'B':
            mask = 0x10
        status = struct.unpack('b', b)[0]
        if verbose:
            print('Lock status(bit4 and bit5):', hex(status))
        if status&mask:
            return True
        else:
            return False

    def GetRefSelect(self):
        """
        Description:
            Get the reference selection.
        Outpus:
            - sel (str): 'external' or 'internal'
        """
        cmdbytes = bytearray(1)
        cmdbytes[0] = 0x86
        self._write(cmdbytes)
        b = self._read(1)
        c = self._read(1)
        if self.CheckReadBack(b,1,c) == False:
            return
        s = struct.unpack('b', b)[0]
        if s&1:
            return 'external'
        else:
            return 'internal'
    
    def SetRefSelect(self, sel='external'):
        """
        Description:
            Set the reference.
        Inputs:
            - sel (str): 'external' or 'internal'.
        """
        if sel == 'external':
            s = 1
        elif sel == 'internal':
            s = 0
        else:
            print('Invalid option.')
            return
        cmdbytes = bytearray(3)
        cmdbytes[0] = 0x06
        cmdbytes[1] = s & 1
        cmdbytes[2] = self._generate_checksum(cmdbytes[:2])
        self._write(cmdbytes)
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

    def Flash(self):
        cmdbytes = bytearray(2)
        cmdbytes[0] = 0x40
        cmdbytes[1] = self._generate_checksum([cmdbytes[0]])
        self._write(cmdbytes)
        r = self._read(1)
        r = struct.unpack('b', r)[0]
        if r == V500X.REPLY['ACK']:
            return True
        else:
            return False

class V5007(V500X):
    """
    Description:
        The communication protocol for V5007 is totally same as V500X.
    """
    pass

class V5008(V500X):
    """
    Description:
        The communication protocol for V5008 is totally same as V500X.
    """
    pass