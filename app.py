from flask import Flask, render_template, request, redirect, url_for
import hashlib
import json
import random
import time

app = Flask(__name__)

class Transaction:
    def __init__(self, amount, payer, payee):
        self.amount = amount
        self.payer = payer  # public key
        self.payee = payee  # public key

    def to_dict(self):
        return {
            'amount': self.amount,
            'payer': self.payer,
            'payee': self.payee
        }

    def to_string(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    def __str__(self):
        return self.to_string()

class TransactionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Transaction):
            return obj.to_dict()
        return super().default(obj)

class Block:
    def __init__(self, prev_hash, transaction):
        self.prev_hash = prev_hash
        self.transaction = transaction
        self.timestamp = time.time()
        self.nonce = random.randint(0, 999999999)

    @property
    def hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True, cls=TransactionEncoder)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __str__(self):
        return f"Block:\n"\
               f"Hash: {self.hash}\n"\
               f"Previous Hash: {self.prev_hash}\n"\
               f"Timestamp: {self.timestamp}\n"\
               f"Nonce: {self.nonce}\n"\
               f"Transaction: {self.transaction}\n"

class Chain:
    instance = None

    @staticmethod
    def get_instance():
        if Chain.instance is None:
            Chain.instance = Chain()
        return Chain.instance

    def __init__(self):
        self.chain = [self.create_genesis_block()]
        
        # Generate a random private key
    genesis_private_key = hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()

    # Derive the public key from the private key
    genesis_public_key = hashlib.sha256(genesis_private_key.encode()).hexdigest()

    GENESIS_PUBLIC_KEY = genesis_public_key  # Set the public key of the genesis block here

    def create_genesis_block(self):
        return Block('', Transaction(100, Chain.GENESIS_PUBLIC_KEY, satoshi.public_key))

    @property
    def last_block(self):
        return self.chain[-1]

    def mine(self, nonce):
        solution = 1
        print('⛏️  mining...')
        while True:
            block_hash = hashlib.md5(str(nonce + solution).encode()).hexdigest()
            if block_hash[:4] == '0000':
                print(f'Solved: {solution}')
                return solution
            solution += 1

    def add_block(self, transaction, sender_public_key, signature):
        if self.verify_transaction(transaction, sender_public_key, signature):
            new_block = Block(self.last_block.hash, transaction)
            new_block.nonce = self.mine(new_block.nonce)
            self.chain.append(new_block)

    def verify_transaction(self, transaction, sender_public_key, signature):
        # In this example, just assume transaction is always valid
        return True

class Wallet:
    def __init__(self, private_key=None):
        if private_key:
            self.private_key = private_key
            self.public_key = self.generate_public_key(private_key)
        else:
            self.public_key, self.private_key = self.generate_key_pair()

    def generate_public_key(self, private_key):
        return hashlib.sha256(private_key.encode()).hexdigest()

    def generate_key_pair(self):
        private_key = hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()
        public_key = self.generate_public_key(private_key)
        return public_key, private_key

    def send_money(self, amount, payee_public_key):
        # Check if it's the genesis transaction
        if self.public_key == Chain.GENESIS_PUBLIC_KEY:
            # Proceed with the transaction without checking balance
            transaction = Transaction(amount, self.public_key, payee_public_key)
            signature = self.sign_transaction(transaction)
            Chain.get_instance().add_block(transaction, self.public_key, signature)
            return "Genesis Transaction Successful"
        
        # For other transactions, check if the sender's wallet has sufficient funds
        if self.get_balance() >= amount:
            transaction = Transaction(amount, self.public_key, payee_public_key)
            signature = self.sign_transaction(transaction)
            Chain.get_instance().add_block(transaction, self.public_key, signature)
            return "Transaction Successful"
        else:
            return "Error: Insufficient Funds"

    def get_balance(self):
        balance = 0
        chain_instance = Chain.get_instance()
        for block in chain_instance.chain:
            if block.transaction.payer == self.public_key:
                balance -= block.transaction.amount
            elif block.transaction.payee == self.public_key:
                balance += block.transaction.amount
        return balance


    def sign_transaction(self, transaction):
        return hashlib.sha256(transaction.to_string().encode()).hexdigest()

# Example usage

satoshi = Wallet()
bob = Wallet()
alice = Wallet()

satoshi.send_money(50, bob.public_key)
bob.send_money(23, alice.public_key)
alice.send_money(5, bob.public_key)

# chain_instance = Chain.get_instance()
# for block in chain_instance.chain:
#    print(block)


@app.route('/')
def index():
    chain_instance = Chain.get_instance()
    chain_data = []
    for block in chain_instance.chain:
        chain_data.append({
            'hash': block.hash,
            'prev_hash': block.prev_hash,
            'timestamp': block.timestamp,
            'nonce': block.nonce,
            'transaction': block.transaction.to_dict()
        })

    # Get the public keys of the wallets
    satoshi_public_key = satoshi.public_key
    bob_public_key = bob.public_key
    alice_public_key = alice.public_key
    
     # Get the balances of the wallets
    satoshi_balance = satoshi.get_balance()
    bob_balance = bob.get_balance()
    alice_balance = alice.get_balance()
    
     # Get the message from the query parameter
    message = request.args.get('message', None)

    return render_template('index.html', chain_data=chain_data, 
                           satoshi_public_key=satoshi_public_key, 
                           bob_public_key=bob_public_key, 
                           alice_public_key=alice_public_key,
                           satoshi_balance=satoshi_balance,
                           bob_balance=bob_balance,
                           alice_balance=alice_balance,
                           message=message)

@app.route('/send_money', methods=['POST'])
def send_money():
    amount = float(request.form['amount'])
    recipient_public_key = request.form['recipient_public_key']
    private_key = request.form['private_key']
    
    # Perform the transaction
    current_wallet = Wallet(private_key)
    message = current_wallet.send_money(amount, recipient_public_key)
    
    # Redirect back to the home page after the transaction is completed
    return redirect(url_for('index', message=message))

if __name__ == '__main__':
    app.run(debug=True)