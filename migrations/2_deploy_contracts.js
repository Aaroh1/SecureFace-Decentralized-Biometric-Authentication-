const BiometricStorage = artifacts.require("BiometricStorage"); // ✅ Matches contract name

module.exports = function (deployer) {
  deployer.deploy(BiometricStorage);
};
