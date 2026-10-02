export class Suggester {
  constructor(snapshot) {
    this.snapshot = snapshot;
  }

  resolve(_query) {
    throw new Error("suggestion capability not implemented");
  }
}
