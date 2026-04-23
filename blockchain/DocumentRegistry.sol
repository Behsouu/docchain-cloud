// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DocumentRegistry {
    
    struct Document {
        bytes32 hash;
        address uploader;
        uint256 timestamp;
        string filename;
    }
    
    mapping(bytes32 => Document) private documents;
    address public owner;
    uint256 public documentCount;
    
    event DocumentRegistered(
        bytes32 indexed hash,
        address indexed uploader,
        uint256 timestamp,
        string filename
    );
    
    constructor() {
        owner = msg.sender;
        documentCount = 0;
    }
    
    function registerDocument(bytes32 _hash, string memory _filename) public {
        require(documents[_hash].timestamp == 0, "Document deja enregistre");
        
        documents[_hash] = Document({
            hash: _hash,
            uploader: msg.sender,
            timestamp: block.timestamp,
            filename: _filename
        });
        
        documentCount++;
        emit DocumentRegistered(_hash, msg.sender, block.timestamp, _filename);
    }
    
    function verifyDocument(bytes32 _hash) public view returns (
        bool exists,
        address uploader,
        uint256 timestamp,
        string memory filename
    ) {
        Document memory doc = documents[_hash];
        if (doc.timestamp == 0) {
            return (false, address(0), 0, "");
        }
        return (true, doc.uploader, doc.timestamp, doc.filename);
    }
    
    function getDocumentCount() public view returns (uint256) {
        return documentCount;
    }
}