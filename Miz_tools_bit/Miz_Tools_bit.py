# -*- coding: utf-8 -*-
'''
Made by Mizogg Tools to Help Look for Bitcoin. Good Luck and Happy Hunting Miz_Tools_bit.py Version 1

Using Bit Library made in Python
https://mizogg.co.uk
'''
import requests, codecs, hashlib, ecdsa, bip32utils, binascii, sys, time, random
from bit.base58 import b58decode_check
from bit.utils import bytes_to_hex
from bit import *
from bit.format import bytes_to_wif
from mnemonic import Mnemonic
from urllib.request import urlopen
from time import sleep

def get_balance(addr):
    contents = requests.get('https://sochain.com/api/v2/get_address_balance/BTC/' + addr, timeout=10)
    res = contents.json()
    response = (contents.content)
    balance = dict(res['data'])['confirmed_balance']
    return balance

class BrainWallet:

    @staticmethod
    def generate_address_from_passphrase(passphrase):
        private_key = str(hashlib.sha256(
            passphrase.encode('utf-8')).hexdigest())
        address =  BrainWallet.generate_address_from_private_key(private_key)
        return private_key, address

    @staticmethod
    def generate_address_from_private_key(private_key):
        public_key = BrainWallet.__private_to_public(private_key)
        address = BrainWallet.__public_to_address(public_key)
        return address

    @staticmethod
    def __private_to_public(private_key):
        private_key_bytes = codecs.decode(private_key, 'hex')
        # Get ECDSA public key
        key = ecdsa.SigningKey.from_string(
            private_key_bytes, curve=ecdsa.SECP256k1).verifying_key
        key_bytes = key.to_string()
        key_hex = codecs.encode(key_bytes, 'hex')
        # Add bitcoin byte
        bitcoin_byte = b'04'
        public_key = bitcoin_byte + key_hex
        return public_key

    @staticmethod
    def __public_to_address(public_key):
        public_key_bytes = codecs.decode(public_key, 'hex')
        # Run SHA256 for the public key
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()
        # Run ripemd160 for the SHA256
        ripemd160_bpk = hashlib.new('ripemd160')
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()
        ripemd160_bpk_hex = codecs.encode(ripemd160_bpk_digest, 'hex')
        # Add network byte
        network_byte = b'00'
        network_bitcoin_public_key = network_byte + ripemd160_bpk_hex
        network_bitcoin_public_key_bytes = codecs.decode(
            network_bitcoin_public_key, 'hex')
        # Double SHA256 to get checksum
        sha256_nbpk = hashlib.sha256(network_bitcoin_public_key_bytes)
        sha256_nbpk_digest = sha256_nbpk.digest()
        sha256_2_nbpk = hashlib.sha256(sha256_nbpk_digest)
        sha256_2_nbpk_digest = sha256_2_nbpk.digest()
        sha256_2_hex = codecs.encode(sha256_2_nbpk_digest, 'hex')
        checksum = sha256_2_hex[:8]
        # Concatenate public key and checksum to get the address
        address_hex = (network_bitcoin_public_key + checksum).decode('utf-8')
        wallet = BrainWallet.base58(address_hex)
        return wallet

    @staticmethod
    def base58(address_hex):
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        b58_string = ''
        # Get the number of leading zeros and convert hex to decimal
        leading_zeros = len(address_hex) - len(address_hex.lstrip('0'))
        # Convert hex to decimal
        address_int = int(address_hex, 16)
        # Append digits to the start of string
        while address_int > 0:
            digit = address_int % 58
            digit_char = alphabet[digit]
            b58_string = digit_char + b58_string
            address_int //= 58
        # Add '1' for each 2 leading zeros
        ones = leading_zeros // 2
        for one in range(ones):
            b58_string = '1' + b58_string
        return b58_string

def data_wallet():
    for child in range(0,20):
        bip32_root_key_obj = bip32utils.BIP32Key.fromEntropy(seed)
        bip32_child_key_obj = bip32_root_key_obj.ChildKey(
            44 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            0 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            0 + bip32utils.BIP32_HARDEN
        ).ChildKey(0).ChildKey(child)
        data.append({
                'bip32_root_key': bip32_root_key_obj.ExtendedKey(),
                'bip32_extended_private_key': bip32_child_key_obj.ExtendedKey(),
                'path': f"m/44'/0'/0'/0/{child}",
                'address': bip32_child_key_obj.Address(),
                'publickey': binascii.hexlify(bip32_child_key_obj.PublicKey()).decode(),
                'privatekey': bip32_child_key_obj.WalletImportFormat(),
            })

"""
@author: iceland
"""

def get_rs(sig):
    rlen = int(sig[2:4], 16)
    r = sig[4:4+rlen*2]
#    slen = int(sig[6+rlen*2:8+rlen*2], 16)
    s = sig[8+rlen*2:]
    return r, s
    
def split_sig_pieces(script):
    sigLen = int(script[2:4], 16)
    sig = script[2+2:2+sigLen*2]
    r, s = get_rs(sig[4:])
    pubLen = int(script[4+sigLen*2:4+sigLen*2+2], 16)
    pub = script[4+sigLen*2+2:]
    assert(len(pub) == pubLen*2)
    return r, s, pub


# Returns list of this list [first, sig, pub, rest] for each input
def parseTx(txn):
    if len(txn) <130:
        print('[WARNING] rawtx most likely incorrect. Please check..')
        sys.exit(1)
    inp_list = []
    ver = txn[:8]
    if txn[8:12] == '0001':
        print('UnSupported Tx Input. Presence of Witness Data')
        sys.exit(1)
    inp_nu = int(txn[8:10], 16)
    
    first = txn[0:10]
    cur = 10
    for m in range(inp_nu):
        prv_out = txn[cur:cur+64]
        var0 = txn[cur+64:cur+64+8]
        cur = cur+64+8
        scriptLen = int(txn[cur:cur+2], 16)
        script = txn[cur:2+cur+2*scriptLen] #8b included
        r, s, pub = split_sig_pieces(script)
        seq = txn[2+cur+2*scriptLen:10+cur+2*scriptLen]
        inp_list.append([prv_out, var0, r, s, pub, seq])
        cur = 10+cur+2*scriptLen
    rest = txn[cur:]
    return [first, inp_list, rest]

#==============================================================================
def get_rawtx_from_blockchain(txid):
    try:
        htmlfile = urlopen("https://blockchain.info/rawtx/%s?format=hex" % txid, timeout = 20)
    except:
        print('Unable to connect internet to fetch RawTx. Exiting..')
        sys.exit(1)
    else: res = htmlfile.read().decode('utf-8')
    return res
# =============================================================================

def getSignableTxn(parsed):
    res = []
    first, inp_list, rest = parsed
    tot = len(inp_list)
    for one in range(tot):
        e = first
        for i in range(tot):
            e += inp_list[i][0] # prev_txid
            e += inp_list[i][1] # var0
            if one == i: 
                e += '1976a914' + HASH160(inp_list[one][4]) + '88ac'
            else:
                e += '00'
            e += inp_list[i][5] # seq
        e += rest + "01000000"
        z = hashlib.sha256(hashlib.sha256(bytes.fromhex(e)).digest()).hexdigest()
        res.append([inp_list[one][2], inp_list[one][3], z, inp_list[one][4], e])
    return res
#==============================================================================
def HASH160(pubk_hex):
    return hashlib.new('ripemd160', hashlib.sha256(bytes.fromhex(pubk_hex)).digest() ).hexdigest()

prompt= '''
    ************************ Main Menu Mizogg's Tools ***************************
    *                       Single Check Tools                                  *
    *    Option 1.Bitcoin Address with Balance Check                   =  1     *
    *    Option 2.Bitcoin Address to HASH160                           =  2     *
    *    Option 3.HASH160 to Bitcoin Address(Not Working)              =  3     *
    *    Option 4.Brain Wallet Bitcoin with Balance Check              =  4     *
    *    Option 5.Hexadecimal to Decimal (HEX 2 DEC)                   =  5     *
    *    Option 6.Decimal to Hexadecimal (DEC 2 HEX)                   =  6     *
    *    Option 7.Hexadecimal to Bitcoin Address with Balance Check    =  7     *
    *    Option 8.Decimal to Bitcoin Address with Balance Check        =  8     *
    *    Option 9.Mnemonic Words to Bitcoin Address with Balance Check =  9     *    
    *    Option 10.WIF to Bitcoin Address with Balance Check           =  10    *
    *    Option 11.Retrieve ECDSA signature R,S,Z rawtx or txid tool   =  11    *
    *                                                                           *
    *                    Generators & Multi Check Tools                         *
    *    Option 12.Bitcoin Addresses from file with Balance Check      = 12     *
    *    Option 13.Bitcoin Addresses from file to HASH160 file         = 13     *
    *    Option 14.Brain Wallet list from file with Balance Check      = 14     *
    *    Option 15.Mnemonic Words Generator Random Choice [Offline]    = 15     *
    *    Option 16.Bitcoin random scan randomly in Range [Offline]     = 16     *
    *    Option 17.Bitcoin Sequence scan sequentially [Offline]        = 17     *
    *                                                                           *
    ******** Main Menu Mizogg's Tools Using Bit Library made in Python **********

Type You Choice Here Enter 1-17 : 
'''


while True:
    data = []
    mylist = []
    count=0
    ammount = 0.00000000
    total= 0
    iteration = 0
    start_time = time.time()
    start=int(input(prompt))
    if start == 1:
        print ('Address Balance Check Tool')
        addr = str(input('Enter Your Bitcoin Address Here : '))
        print ('\nBitcoin Address = ', addr, '    Balance = ', get_balance(addr), ' BTC')
    elif start == 2:
        print ('Address to HASH160 Tool')
        addr = str(input('Enter Your Bitcoin Address Here : '))
        hash160=b58decode_check(addr)
        address_hash160 = bytes_to_hex(hash160)[2:]
        print ('\nBitcoin Address = ', addr, '\nTo HASH160 = ', address_hash160)
    elif start == 3:
        print ('HASH160 to Bitcoin Address Tool')
        hash160 =(str(input('Enter Your HASH160 Here : ')))
        print ('Coming Soon not Working')
    elif start == 4:
        print ('Brain Wallet Bitcoin Address Tool')    
        passphrase = (input("'Type Your Passphrase HERE : "))
        wallet = BrainWallet()
        private_key, addr = wallet.generate_address_from_passphrase(passphrase)
        print('\nPassphrase     = ',passphrase)
        print('Private Key      = ',private_key)
        print('Bitcoin Address  = ', addr, '    Balance = ', get_balance(addr), ' BTC')
    elif start == 5:
        print('Hexadecimal to Decimal Tool')
        HEX = str(input('Enter Your Hexadecimal HEX Here : '))
        dec = int(HEX, 16)
        print('\nHexadecimal = ',HEX, '\nTo Decimal = ', dec)
    elif start == 6:
        print('Decimal to Hexadecimal Tool')
        dec = int(input('Enter Your Decimal DEC Here : '))
        HEX = "%064x" % dec
        print('\nDecimal = ', dec, '\nTo Hexadecimal = ', HEX)
    elif start == 7:
        print('Hexadecimal to Bitcoin Address Tool')
        HEX=str(input("Hexadecimal HEX ->  "))
        dec = int(HEX, 16)
        key = Key.from_int(dec)
        wifu = bytes_to_wif(key.to_bytes(), compressed=False)
        wifc = bytes_to_wif(key.to_bytes(), compressed=True)
        key1 = Key(wifu)
        caddr = key.address
        uaddr = key1.address
        saddr = key.segwit_address
        query = {caddr}|{uaddr}|{saddr}
        request = requests.get("https://blockchain.info/multiaddr?active=" + ','.join(query), timeout=10)
        try:
            request = request.json()
            print('PrivateKey (hex) : ', HEX)
            print('PrivateKey (dec) : ', dec)
            print('PrivateKey (wif) Compressed   : ', wifc)
            print('PrivateKey (wif) UnCompressed : ', wifu)
            print('Bitcoin Address Compressed   = ', caddr, '    Balance = ', get_balance(caddr), ' BTC')
            print('Bitcoin Address UnCompressed = ', uaddr, '    Balance = ', get_balance(uaddr), ' BTC')
            print('Bitcoin Address Segwit       = ', saddr, '    Balance = ', get_balance(saddr), ' BTC')
            for row in request["addresses"]:
                print(row)
        except:
            pass
    elif start == 8:
        print('Decimal to Bitcoin Address Tool')
        dec=int(input('Decimal Dec (Max 115792089237316195423570985008687907852837564279074904382605163141518161494336 ) ->  '))
        HEX = "%064x" % dec  
        key = Key.from_int(dec)
        wifu = bytes_to_wif(key.to_bytes(), compressed=False)
        wifc = bytes_to_wif(key.to_bytes(), compressed=True)
        key1 = Key(wifu)
        caddr = key.address
        uaddr = key1.address
        saddr = key.segwit_address
        query = {caddr}|{uaddr}|{saddr}
        request = requests.get("https://blockchain.info/multiaddr?active=" + ','.join(query), timeout=10)
        try:
            request = request.json()
            print('PrivateKey (hex) : ', HEX)
            print('PrivateKey (dec) : ', dec)
            print('PrivateKey (wif) Compressed   : ', wifc)
            print('PrivateKey (wif) UnCompressed : ', wifu)
            print('Bitcoin Address Compressed   = ', caddr, '    Balance = ', get_balance(caddr), ' BTC')
            print('Bitcoin Address UnCompressed = ', uaddr, '    Balance = ', get_balance(uaddr), ' BTC')
            print('Bitcoin Address Segwit       = ', saddr, '    Balance = ', get_balance(saddr), ' BTC')
            for row in request["addresses"]:
                print(row)
        except:
            pass
    elif start == 9:
        print('Mnemonic 12/15/18/21/24 Words to Bitcoin Address Tool')
        wordlist = str(input('Enter Your Mnemonic Words = '))
        mnemo = Mnemonic("english")
        mnemonic_words = wordlist
        seed = mnemo.to_seed(mnemonic_words, passphrase="")
        data_wallet()
        for target_wallet in data:
            print('\nmnemonic_words  : ', mnemonic_words, '\nDerivation Path : ', target_wallet['path'], '\nBitcoin Address : ', target_wallet['address'], ' Balance = ', get_balance(target_wallet['address']), ' BTC', '\nPrivatekey WIF  : ', target_wallet['privatekey'])    
    elif start == 10:
        print('WIF to Bitcoin Address Tool')
        WIF = str(input('Enter Your Wallet Import Format WIF = '))
        addr = Key(WIF).address
        print('\nWallet Import Format WIF = ', WIF)
        print('Bitcoin Address  = ', addr, '    Balance = ', get_balance(addr), ' BTC')
    elif start == 11:
        promptrsz= '''
    ************************* Retrieve ECDSA signature R,S,Z rawtx or txid tool ************************* 
    *                                                                                                   *
    *    1-txid  blockchain API R,S,Z calculation starts. [Internet required]                           *
    *    2-rawtx R,S,Z,Pubkey for each of the inputs present in the rawtx data. [No Internet required]  *
    *    Type 1-2 to Start                                                                              *
    *                                                                                                   *
    ************************* Retrieve ECDSA signature R,S,Z rawtx or txid tool *************************
        '''
        startrsz=int(input(promptrsz))
        if startrsz == 1:
            txid = str(input('Enter Your -txid = ')) #'82e5e1689ee396c8416b94c86aed9f4fe793a0fa2fa729df4a8312a287bc2d5e'
            rawtx = get_rawtx_from_blockchain(txid)
        elif startrsz == 2:
            rawtx =str(input('Enter Your -rawtx = ')) #'01000000028370ef64eb83519fd14f9d74826059b4ce00eae33b5473629486076c5b3bf215000000008c4930460221009bf436ce1f12979ff47b4671f16b06a71e74269005c19178384e9d267e50bbe9022100c7eabd8cf796a78d8a7032f99105cdcb1ae75cd8b518ed4efe14247fb00c9622014104e3896e6cabfa05a332368443877d826efc7ace23019bd5c2bc7497f3711f009e873b1fcc03222f118a6ff696efa9ec9bb3678447aae159491c75468dcc245a6cffffffffb0385cd9a933545628469aa1b7c151b85cc4a087760a300e855af079eacd25c5000000008b48304502210094b12a2dd0f59b3b4b84e6db0eb4ba4460696a4f3abf5cc6e241bbdb08163b45022007eaf632f320b5d9d58f1e8d186ccebabea93bad4a6a282a3c472393fe756bfb014104e3896e6cabfa05a332368443877d826efc7ace23019bd5c2bc7497f3711f009e873b1fcc03222f118a6ff696efa9ec9bb3678447aae159491c75468dcc245a6cffffffff01404b4c00000000001976a91402d8103ac969fe0b92ba04ca8007e729684031b088ac00000000'
        else:
            print("WRONG NUMBER!!! MUST CHOSE 1 - 2 ")
            break

        print('\nStarting Program...')

        m = parseTx(rawtx)
        e = getSignableTxn(m)

        for i in range(len(e)):
            print('='*70,f'\n[Input Index #: {i}]\n     R: {e[i][0]}\n     S: {e[i][1]}\n     Z: {e[i][2]}\nPubKey: {e[i][3]}')
    elif start == 12:
        promptchk= '''
    ************************* Bitcoin Addresses from file with Balance Check ************************* 
    *                                                                                                *
    *    ** This Tool needs a file called bct.txt with a list of Bitcoin Addresses                   *
    *    ** Your list of addresses will be check for Balance [Internet required]                     *
    *    ** ANY BITCOIN WALLETS FOUND WITH BALANCE WILL BE SAVE TO (balance.txt)                     *
    *                                                                                                *
    ************************* Bitcoin Addresses from file with Balance Check *************************
        '''
        print(promptchk)
        time.sleep(0.5)
        print('Bitcoin Addresses loading please wait..................................:')
        with open("btc.txt", "r") as file:
            line_count = 0
            for line in file:
                line != "\n"
                line_count += 1
        with open('btc.txt', newline='', encoding='utf-8') as f:
            for line in f:
                mylist.append(line.strip())
        print('Total Bitcoin Addresses Loaded now Checking Balance ', line_count)
        remaining=line_count
        for i in range(0,len(mylist)):
            count+=1
            remaining-=1
            addr = mylist[i]
            time.sleep(0.5)
            if float (get_balance(addr)) > ammount:
                print ('\nBitcoin Address = ', addr, '    Balance = ', get_balance(addr), ' BTC')
                f=open('balance.txt','a')
                f.write('\nBitcoin Address = ' + addr + '    Balance = ' + get_balance(addr) + ' BTC')
                f.close()
            else:
                print ('\nScan Number = ',count, ' == Remaining = ', remaining)
                print ('\nBitcoin Address = ', addr, '    Balance = ', get_balance(addr), ' BTC')
    elif start == 13:
        prompthash= '''
    *********************** Bitcoin Addresses from file to HASH160 file Tool ************************* 
    *                                                                                                *
    *    ** This Tool needs a file called bct.txt with a list of Bitcoin Addresses                   *
    *    ** Your list of addresses will be converted to HASH160 [NO Internet required]               *
    *    ** HASH160 Addressess will be saved to a file called hash160.txt                            *
    *                                                                                                *
    *********************** Bitcoin Addresses from file to HASH160 file Tool *************************
        '''
        print(prompthash)
        time.sleep(0.5)
        print('Bitcoin Addresses loading please wait..................................:')
        with open("btc.txt", "r") as file:
            line_count = 0
            for line in file:
                line != "\n"
                line_count += 1
        with open('btc.txt', newline='', encoding='utf-8') as f:
            for line in f:
                mylist.append(line.strip())
        print('Total Bitcoin Addresses Loaded now Converting to HASH160 ', line_count)
        remaining=line_count
        for i in range(0,len(mylist)):
            count+=1
            remaining-=1
            addr = mylist[i]
            hash160=b58decode_check(addr)
            address_hash160 = bytes_to_hex(hash160)[2:]
            print ('\nBitcoin Address = ', addr, '\nTo HASH160 = ', address_hash160)
            f=open('hash160.txt','a')
            f.write('\n' + address_hash160)
            f.close()
    elif start == 14:
        promptbrain= '''
    *********************** Brain Wallet list from file with Balance Check Tool **********************
    *                                                                                                *
    *    ** This Tool needs a file called brainwords.txt with a list of Brain Wallet words           *
    *    ** Your list will be converted to Bitcoin and Balance Checked [Internet required]           *
    *    ** ANY BRAIN WALLETS FOUND WITH BALANCE WILL BE SAVE TO (winner.txt)                        *
    *                                                                                                *
    *********************** Brain Wallet list from file with Balance Check Tool **********************
        '''
        print(promptbrain)
        time.sleep(0.5)
        print('BRAIN WALLET PASSWORD LIST LOADING>>>>')
        with open("brainwords.txt", "r") as file:
            line_count = 0
            for line in file:
                line != "\n"
                line_count += 1
        with open('brainwords.txt', newline='', encoding='utf-8') as f:
            for line in f:
                mylist.append(line.strip())
        print('Total Brain Wallet Password Loaded:', line_count)
        remaining=line_count
        for i in range(0,len(mylist)):
            time.sleep(0.5)
            count+=1
            remaining-=1
            passphrase = mylist[i]
            wallet = BrainWallet()
            private_key, addr = wallet.generate_address_from_passphrase(passphrase)
            if float (get_balance(addr)) > ammount:
                print ('\nBitcoin Address = ', addr, '    Balance = ', get_balance(addr), ' BTC')
                print('Passphrase       : ',passphrase)
                print('Private Key      : ',private_key)
                print('Scan Number : ', count, ' : Remaing Passwords : ', remaining)
                f=open('winner.txt','a')
                f.write('\nBitcoin Address = ' + addr + '    Balance = ' + get_balance(addr) + ' BTC')
                f.write('\nPassphrase       : '+ passphrase)
                f.write('\nPrivate Key      : '+ private_key)
                f.close()
            else:
                print ('\nScan Number = ',count, ' == Remaining = ', remaining)
                print ('\nBitcoin Address = ', addr, '    Balance = ', get_balance(addr), ' BTC')
    elif start == 15:
        promptMnemonic= '''
    *********************** Mnemonic Words Generator Random [Offline] *****************************
    *                                                                                             *
    *    ** This Tool needs a file called bct.txt with a list of Bitcoin Addresses Database       *
    *    ** ANY MNEMONIC WORDS FOUND THAT MATCH BTC DATABASE WILL SAVE TO  (winner.txt)           *
    *                                                                                             *
    *********************** Mnemonic Words Generator Random [Offline] *****************************
        '''
        print(promptMnemonic)
        time.sleep(0.5)
        filename ='btc.txt'
        with open(filename) as f:
            line_count = 0
            for line in f:
                line != "\n"
                line_count += 1        
        with open(filename) as file:
            add = file.read().split()
        add = set(add)
        print('Total Bitcoin Addresses Loaded ', line_count)        
        print('Mnemonic 12/15/18/21/24 Words to Bitcoin Address Tool')
        R = int(input('Enter Ammount Mnemonic Words 12/15/18/21/24 : '))
        if R == 12:
            s1 = 128
        elif R == 15:
            s1 = 160
        elif R == 18:
            s1 = 192
        elif R == 21:
            s1 = 224
        elif R == 24:
            s1 = 256
        else:
            print("WRONG NUMBER!!! Starting with 24 Words")
            s1 = 256
        while True:
            data=[]
            count += 1
            total += 20
            mnemo = Mnemonic("english")
            mnemonic_words = mnemo.generate(strength=s1)
            seed = mnemo.to_seed(mnemonic_words, passphrase="")
            entropy = mnemo.to_entropy(mnemonic_words)
            data_wallet()
            for target_wallet in data:
                address = target_wallet['address']
                if address in add:
                    print('\nMatch Found')
                    print('\nmnemonic_words  : ', mnemonic_words)
                    print('Derivation Path : ', target_wallet['path'], ' : Bitcoin Address : ', target_wallet['address'])
                    print('Privatekey WIF  : ', target_wallet['privatekey'])
                    with open("winner.txt", "a") as f:
                        f.write(f"""\nMnemonic_words:  {mnemonic_words}
                        Derivation Path:  {target_wallet['path']}
                        Privatekey WIF:  {target_wallet['privatekey']}
                        Public Address Bitcoin:  {target_wallet['address']}
                        =====Made by mizogg.co.uk Donations 3P7PZLbwSt2bqUMsHF9xDsaNKhafiGuWDB =====""")
            else:
                print(' [' + str(count) + '] ------------------------')
                print('Total Checked [' + str(total) + '] ')
                print('\nmnemonic_words  : ', mnemonic_words)
                for bad_wallet in data:
                    print('Derivation Path : ', bad_wallet['path'], ' : Bitcoin Address : ', bad_wallet['address'])
                    print('Privatekey WIF  : ', bad_wallet['privatekey'])
    elif start == 16:
        promptrandom= '''
    *********************** Bitcoin random scan randomly in Range Tool ************************
    *                                                                                         *
    *    ** Bitcoin random scan randomly in Range [Offline]                                   *
    *    ** This Tool needs a file called bct.txt with a list of Bitcoin Addresses Database   *
    *    ** ANY MATCHING WALLETS GENERATED THAT MATCH BTC DATABASE WILL SAVE TO(winner.txt)   *
    *                                                                                         *
    **************[+] Starting.........Please Wait.....Bitcoin Address List Loading.....*******
        '''
        print(promptrandom)
        time.sleep(0.5)
        filename ='btc.txt'
        with open(filename) as f:
            line_count = 0
            for line in f:
                line != "\n"
                line_count += 1
        with open(filename) as file:
            add = file.read().split()
        add = set(add)
        print('Total Bitcoin Addresses Loaded and Checking : ',str (line_count)) 
        start=int(input("start range Min 1-115792089237316195423570985008687907852837564279074904382605163141518161494335 ->  "))
        stop=int(input("stop range Max 115792089237316195423570985008687907852837564279074904382605163141518161494336 -> "))
        print("Starting search... Please Wait min range: " + str(start))
        print("Max range: " + str(stop))
        print("==========================================================")
        print('Total Bitcoin Addresses Loaded and Checking : ',str (line_count))    
        while True:
            count += 3
            iteration += 1
            dec=random.randrange(start,stop)
            HEX = "%064x" % dec  
            key = Key.from_int(dec)
            wifu = bytes_to_wif(key.to_bytes(), compressed=False)
            wifc = bytes_to_wif(key.to_bytes(), compressed=True)
            key1 = Key(wifu)
            caddr = key.address
            uaddr = key1.address
            saddr = key.segwit_address
            if caddr in add or uaddr in add or saddr in add:
                print('\nMatch Found')
                print('\nPrivatekey (dec): ', dec,'\nPrivatekey (hex): ', HEX, '\nPrivatekey Uncompressed: ', wifu, '\nPrivatekey compressed: ', wifc, '\nPublic Address 1 Uncompressed: ', uaddr, '\nPublic Address 1 Compressed: ', caddr, '\nPublic Address 3 P2SH: ', saddr)
                f=open("winner.txt","a")
                f.write('\nPrivatekey (dec): ' + str(dec))
                f.write('\nPrivatekey (hex): ' + HEX)
                f.write('\nPrivatekey Uncompressed: ' + wifu)
                f.write('\nPrivatekey compressed: ' + wifc)
                f.write('\nPublic Address 1 Compressed: ' + caddr)
                f.write('\nPublic Address 1 Uncompressed: ' + uaddr)
                f.write('\nPublic Address 3 P2SH: ' + saddr)
            else:
                if iteration % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f'It/CPU={iteration} checked={count} Hex={HEX} Keys/Sec={iteration / elapsed:.1f}')
    elif start == 17:
        promptsequence= '''
    *********************** Bitcoin sequence Divison in Range Tool ****************************
    *                                                                                         *
    *    ** Bitcoin sequence scan sequentially in Range [Offline]                             *
    *    ** This Tool needs a file called bct.txt with a list of Bitcoin Addresses Database   *
    *    ** ANY MATCHING WALLETS GENERATED THAT MATCH BTC DATABASE WILL SAVE TO(winner.txt)   *
    *                                                                                         *
    **************[+] Starting.........Please Wait.....Bitcoin Address List Loading.....*******
        '''
        print(promptsequence)
        time.sleep(0.5)
        filename ='btc.txt'
        with open(filename) as f:
            line_count = 0
            for line in f:
                line != "\n"
                line_count += 1
        with open(filename) as file:
            add = file.read().split()
        add = set(add)
        print('Total Bitcoin Addresses Loaded and Checking : ',str (line_count)) 
        start=int(input("start range Min 1-115792089237316195423570985008687907852837564279074904382605163141518161494335 ->  "))
        stop=int(input("stop range Max 115792089237316195423570985008687907852837564279074904382605163141518161494336 -> "))
        mag=int(input("Magnitude Jump Stride -> "))
        remainingtotal=stop-start
        while start < stop:
            remainingtotal-=mag
            start+=mag
            count += 3
            iteration += 1
            dec=start
            HEX = "%064x" % dec  
            key = Key.from_int(dec)
            wifu = bytes_to_wif(key.to_bytes(), compressed=False)
            wifc = bytes_to_wif(key.to_bytes(), compressed=True)
            key1 = Key(wifu)
            caddr = key.address
            uaddr = key1.address
            saddr = key.segwit_address
            if caddr in add or uaddr in add or saddr in add:
                print('\nMatch Found')
                print('\nPrivatekey (dec): ', dec,'\nPrivatekey (hex): ', HEX, '\nPrivatekey Uncompressed: ', wifu, '\nPrivatekey compressed: ', wifc, '\nPublic Address 1 Uncompressed: ', uaddr, '\nPublic Address 1 Compressed: ', caddr, '\nPublic Address 3 P2SH: ', saddr)
                f=open("winner.txt","a")
                f.write('\nPrivatekey (dec): ' + str(dec))
                f.write('\nPrivatekey (hex): ' + HEX)
                f.write('\nPrivatekey Uncompressed: ' + wifu)
                f.write('\nPrivatekey compressed: ' + wifc)
                f.write('\nPublic Address 1 Compressed: ' + caddr)
                f.write('\nPublic Address 1 Uncompressed: ' + uaddr)
                f.write('\nPublic Address 3 P2SH: ' + saddr)
            else:
                if iteration % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f'It/CPU={iteration} checked={count} Hex={HEX} Keys/Sec={iteration / elapsed:.1f}')
            
            
            
    else:
        print("WRONG NUMBER!!! MUST CHOSE 1 - 17 ")
        break