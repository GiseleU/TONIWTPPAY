declare module '*.png' {
  const value: string;
  export default value;
}
// tells TypeScript that any .png import is a string (the URL).