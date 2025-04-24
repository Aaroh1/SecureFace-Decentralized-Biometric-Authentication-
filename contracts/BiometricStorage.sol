// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BiometricStorage {
    mapping(string => string) private userIPFSHashes;
    address public owner;

    event IPFSHashStored(string indexed uid, string ipfsHash);
    event IPFSHashUpdated(string indexed uid, string newIpfsHash);
    event IPFSHashRevoked(string indexed uid);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // Store initial IPFS hash
    function storeIPFSHash(string memory uid, string memory ipfsHash) public onlyOwner {
        require(bytes(userIPFSHashes[uid]).length == 0, "IPFS hash already exists");
        userIPFSHashes[uid] = ipfsHash;
        emit IPFSHashStored(uid, ipfsHash);
    }

    // Retrieve stored IPFS hash
    function getIPFSHash(string memory uid) public view returns (string memory) {
        require(bytes(userIPFSHashes[uid]).length != 0, "No IPFS hash found");
        return userIPFSHashes[uid];
    }

    // Update existing IPFS hash with a new one clearly (revocation/update)
    function updateIPFSHash(string memory uid, string memory newIpfsHash) public onlyOwner {
        require(bytes(userIPFSHashes[uid]).length != 0, "No IPFS hash found");
        userIPFSHashes[uid] = newIpfsHash;
        emit IPFSHashUpdated(uid, newIpfsHash);
    }

    // Completely revoke (delete) the stored IPFS hash clearly
    function revokeIPFSHash(string memory uid) public onlyOwner {
        require(bytes(userIPFSHashes[uid]).length != 0, "No IPFS hash found");
        delete userIPFSHashes[uid];
        emit IPFSHashRevoked(uid);
    }
}
