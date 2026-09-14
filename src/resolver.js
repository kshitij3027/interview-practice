export class RouteResolver {
  constructor(catalog) {
    this.catalog = catalog;
  }

  resolve(_query) {
    throw new Error('route resolution is not implemented');
  }
}
