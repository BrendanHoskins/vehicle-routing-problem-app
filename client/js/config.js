export const fileTypes = {
  deliveries: {
    id: "deliveries",
    label: "Deliveries CSV",
    mappings: [
      { value: "uid", label: "UID" },
      { value: "current_location", label: "Current Location" },
      { value: "destination", label: "Destination" },
      { value: "volume", label: "Volume" },
      { value: "weight", label: "Weight" },
    ],
    required: true,
    validationKey: "current_location",
  },
  pickups: {
    id: "pickups",
    label: "Pickups CSV",
    mappings: [
      { value: "uid", label: "UID" },
      { value: "current_location", label: "Current Location" },
      { value: "destination", label: "Destination" },
      { value: "volume", label: "Volume" },
      { value: "weight", label: "Weight" },
    ],
    required: true,
    validationKey: "current_location",
  },
  trucks: {
    id: "trucks",
    label: "Trucks CSV",
    mappings: [
      { value: "uid", label: "Unique Identifier" },
      { value: "max_volume", label: "Max Volume of All Packages" },
      { value: "max_weight", label: "Max Weight of All Packages" },
      { value: "current_location", label: "Current Location" },
      { value: "end_location", label: "End Location" },
      { value: "range", label: "Range (single tank or charge)" },
    ],
    required: true,
    validationKey: "max_volume",
  },
  depots: {
    id: "depots",
    label: "Depots CSV",
    mappings: [
      { value: "uid", label: "UID" },
      { value: "location", label: "Location" },
    ],
    required: true,
    validationKey: "uid",
  }
};

