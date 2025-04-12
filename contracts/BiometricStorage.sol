// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BiometricStorage {
    mapping(string => string) private userIPFSHashes;
    address public owner;

    event IPFSHashStored(string indexed email, string ipfsHash);
    event IPFSHashUpdated(string indexed email, string newIpfsHash);
    event IPFSHashRevoked(string indexed email);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // Store initial IPFS hash
    function storeIPFSHash(string memory email, string memory ipfsHash) public onlyOwner {
        require(bytes(userIPFSHashes[email]).length == 0, "IPFS hash already exists");
        userIPFSHashes[email] = ipfsHash;
        emit IPFSHashStored(email, ipfsHash);
    }

    // Retrieve stored IPFS hash
    function getIPFSHash(string memory email) public view returns (string memory) {
        require(bytes(userIPFSHashes[email]).length != 0, "No IPFS hash found");
        return userIPFSHashes[email];
    }

    // Update existing IPFS hash with a new one clearly (revocation/update)
    function updateIPFSHash(string memory email, string memory newIpfsHash) public onlyOwner {
        require(bytes(userIPFSHashes[email]).length != 0, "No IPFS hash found");
        userIPFSHashes[email] = newIpfsHash;
        emit IPFSHashUpdated(email, newIpfsHash);
    }

    // Completely revoke (delete) the stored IPFS hash clearly
    function revokeIPFSHash(string memory email) public onlyOwner {
        require(bytes(userIPFSHashes[email]).length != 0, "No IPFS hash found");
        delete userIPFSHashes[email];
        emit IPFSHashRevoked(email);
    }
}
/* Compiling your contracts...
===========================
> Compiling .\contracts\BiometricStorage.sol
> Artifacts written to C:\Users\aaroh\OneDrive\Desktop\IIITM\Sem 8\BTP\Code\main code\build\contracts
> Compiled successfully using:
   - solc: 0.8.0+commit.c7dfd78e.Emscripten.clang


Starting migrations...
======================
> Network name:    'sepolia'
> Network id:      11155111
> Block gas limit: 35999965 (0x22550dd)


2_deploy_contracts.js
=====================

   Deploying 'BiometricStorage'
   ----------------------------
   > transaction hash:    0x892b7389acbc848649433e25ef6f9bd29ffa3e5996b58b31cb9e068c3092472e
   > Blocks: 1            Seconds: 13
   > contract address:    0xD02fcd7d83e5A41AE2e39a55382E851AC28C3d11
   > block number:        8095096
   > block timestamp:     1744346052
   > account:             0xB724157e47A7D6518166CD48dB73689c185F1444
   > balance:             0.048082381315297734
   > gas used:            766402 (0xbb1c2)
   > gas price:           2.502105533 gwei
   > value sent:          0 ETH
   > total cost:          0.001917618684702266 ETH

   Pausing for 2 confirmations...

   -------------------------------
   > confirmation number: 1 (block: 8095097)
   > confirmation number: 2 (block: 8095098)
   > Saving artifacts
   -------------------------------------
   > Total cost:     0.001917618684702266 ETH

Summary
=======
> Total deployments:   1
> Final cost:          0.001917618684702266 ETH
 */