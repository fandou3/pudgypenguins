from eth_account.messages import encode_defunct
from eth_account import Account

class WalletManager:
    def __init__(self, private_key=None):
        """
        初始化钱包管理器
        private_key: 可选，如果提供则使用已有私钥，否则生成新钱包
        """
        if private_key:
            self.account = Account.from_key(private_key)
            self.private_key = private_key
        else:
            new_wallet = Account.create()
            self.account = new_wallet
            self.private_key = new_wallet._private_key.hex()
        
        self.address = self.account.address

    def sign_message(self, message):
        """
        对消息进行签名
        
        参数:
        message: 需要签名的消息
        """
        try:
            # 对消息进行编码
            message_encoded = encode_defunct(text=message)
            
            # 签名消息
            signed_message = self.account.sign_message(message_encoded)
            
            # 返回签名结果和地址
            return {
                'address': self.address,
                'private_key': self.private_key,
                'signature': signed_message.signature.hex()
            }
        
        except Exception as e:
            return {'error': str(e)}