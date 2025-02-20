let addresses = [];

function addAddress(address) {
  if (address) {
    addresses.push(address);
    updateAddressList();
  }
}

function deleteAddress(index) {
  addresses.splice(index, 1);
  updateAddressList();
}

function updateAddressList() {
  const addressList = document.getElementById("addressList");
  addressList.innerHTML = "";

  addresses.forEach((address, index) => {
    const addressItem = document.createElement("div");
    addressItem.className = "address-item";
    addressItem.innerHTML = `
            <span>${index + 1}. ${address}</span>
            <button class="delete-btn" onclick="deleteAddress(${index})">Delete</button>
        `;
    addressList.appendChild(addressItem);
  });
}

function getAddresses() {
  return addresses;
}

function setAddresses(newAddresses) {
  addresses = newAddresses;
  updateAddressList();
}

export {
  addAddress,
  deleteAddress,
  updateAddressList,
  getAddresses,
  setAddresses,
};
