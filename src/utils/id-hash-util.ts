import Hashids from 'hashids';

const hashids = new Hashids('your-salt-string', 8); // Use a strong, project-specific salt

export function encodeId(id: number): string {
	return hashids.encode(id);
}

export function decodeId(hash: string): number | undefined {
	const [id] = hashids.decode(hash);
	return typeof id === 'number' ? id : undefined;
}
