const PATH_SEPARATORS = /[\\/]/;

export function fileName(path: string): string {
  return path.split(PATH_SEPARATORS).at(-1) ?? path;
}
