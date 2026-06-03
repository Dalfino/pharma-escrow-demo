const hre = require("hardhat");

async function main() {
  const [buyer, seller, oracle] = await hre.ethers.getSigners();

  const ColdChainEscrow = await hre.ethers.getContractFactory("ColdChainEscrow");
  const escrow = await ColdChainEscrow.deploy(seller.address, oracle.address);
  await escrow.deployed();   // ✅ correct for ethers v5

  console.log("Escrow deployed to:", escrow.address);
  console.log("Buyer address:", buyer.address);
  console.log("Seller address:", seller.address);
  console.log("Oracle address:", oracle.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});