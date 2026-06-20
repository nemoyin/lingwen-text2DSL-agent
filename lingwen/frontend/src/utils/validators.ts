export function required(value: string | undefined | null): boolean {
  return !!value && value.trim().length > 0;
}

export function isValidHost(value: string): boolean {
  const pattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$/;
  return pattern.test(value) || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(value);
}

export function isValidPort(value: number): boolean {
  return Number.isInteger(value) && value >= 1 && value <= 65535;
}
