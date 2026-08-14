import { createApp } from "./app.js";

const port = 3001;
createApp().listen(port, () => {
  console.log(`Dispatch Desk API listening on http://localhost:${port}`);
});
