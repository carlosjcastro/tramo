const integer = new Intl.NumberFormat("es-AR");

export const percent = (value) => Math.round(value * 100);
export const count = (value) => integer.format(value);
export const megabytes = (bytes) => `${integer.format(Number((bytes / 1048576).toFixed(1)))} MB`;
