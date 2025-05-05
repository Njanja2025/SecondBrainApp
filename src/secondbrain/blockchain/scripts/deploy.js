const hre = require("hardhat");

async function main() {
  // Get deployment parameters from environment
  const contractName = process.env.CONTRACT_NAME || "SecondBrainToken";
  const constructorArgs = process.env.CONSTRUCTOR_ARGS ? 
    JSON.parse(process.env.CONSTRUCTOR_ARGS) : [];
  const verify = process.env.VERIFY === "true";
  
  console.log(`Deploying ${contractName}...`);
  console.log("Constructor arguments:", constructorArgs);

  // Get the Contract factory
  const Contract = await hre.ethers.getContractFactory(contractName);
  
  // Deploy the contract
  const contract = await Contract.deploy(...constructorArgs);
  await contract.waitForDeployment();
  
  const address = await contract.getAddress();
  console.log(`${contractName} deployed to:`, address);
  
  // Verify contract if requested and not on localhost
  if (verify && hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("Verifying contract...");
    try {
      await hre.run("verify:verify", {
        address: address,
        constructorArguments: constructorArgs,
      });
      console.log("Contract verified successfully");
    } catch (error) {
      console.error("Contract verification failed:", error);
    }
  }
  
  // Return deployment info
  return {
    name: contractName,
    address: address,
    network: hre.network.name,
    constructorArgs: constructorArgs
  };
}

// Execute deployment
main()
  .then((deploymentInfo) => {
    console.log("Deployment successful:", deploymentInfo);
    process.exit(0);
  })
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  }); 