import { ChatResponseType } from "@/constants/enum";
import { WSEventHandler } from "./event_handler";

export interface ICareerAgentAPI {
  url: string;
  debug: boolean;
}

export class CareerAgentAPI extends WSEventHandler {
  #url: string;
  #debug: boolean;
  #ws: WebSocket | null;
  #isNewMessage: boolean;

  constructor(params: ICareerAgentAPI) {
    super();

    this.#url = params.url;
    this.#debug = !!params.debug;
    this.#ws = null;
    this.#isNewMessage = true;
  }

  isConnected() {
    return !!this.#ws;
  }

  log(...args: Array<any>): boolean {
    const date = new Date().toISOString();
    let logs: Array<any> = [`[Websocket/${date}]`];
    logs = logs.concat(args).map((arg) => {
      if (typeof arg === "object" && arg !== null) {
        return JSON.stringify(arg, null, 2);
      } else {
        return arg;
      }
    });
    if (this.#debug) {
      console.debug(...logs);
    }
    return true;
  }

  async connect(sessionID: string | null = null): Promise<boolean> {
    if (this.isConnected()) {
      return true;
    }
    const endpoint = `${this.#url}${sessionID ? `?session_id=${sessionID}` : ""}`;
    if (globalThis.WebSocket) {
      /**
       * Web browser
       */
      const WebSocket = globalThis.WebSocket;
      let ws: WebSocket | null = null;
      try {
        ws = new WebSocket(endpoint);
      } catch (e: unknown) {
        console.debug("api WebSocket connection failed");
        return Promise.reject(e);
      }
      ws.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        this.receive(message);
      });
      return new Promise((resolve, reject) => {
        const connectionErrorHandler = (e: unknown) => {
          console.debug("ws.error before connect event:", e);
          this.disconnect(ws);
          // To auto reconnect when failing to open a connection
          this.dispatch("close", { error: true });
          reject(new Error(`Could not connect to "${this.#url}"`));
        };
        ws.addEventListener("error", connectionErrorHandler);
        ws.addEventListener("open", () => {
          this.log(`Connected to "${this.#url}"`);
          ws.removeEventListener("error", connectionErrorHandler);
          ws.addEventListener("error", (e: unknown) => {
            console.debug("ws.error event after connect:", e);
            this.disconnect(ws);
            this.log(`Error, disconnected from "${this.#url}"`);
            this.dispatch("close", { error: true });
          });
          ws.addEventListener("close", (event) => {
            this.disconnect(ws);
            this.log(
              `Disconnected from "${this.#url}": ${event.code} ${event.reason}`,
            );
            this.dispatch("close", { error: false });
          });
          this.#ws = ws;
          resolve(true);
        });
      });
    } else {
      /**
       * Node.js
       */
      const moduleName = "ws";
      const wsModule = await import(/* webpackIgnore: true */ moduleName);
      const WebSocket = wsModule.default;
      const ws = new WebSocket(endpoint);
      ws.on("message", (data: MessageEvent<unknown>) => {
        const message = JSON.parse(data.toString());
        this.receive(message);
      });
      return new Promise((resolve, reject) => {
        const connectionErrorHandler = () => {
          this.disconnect(ws);
          reject(new Error(`Could not connect to "${this.#url}"`));
        };
        ws.on("error", connectionErrorHandler);
        ws.on("open", () => {
          this.log(`Connected to "${this.#url}"`);
          ws.removeListener("error", connectionErrorHandler);
          ws.on("error", () => {
            this.disconnect(ws);
            this.log(`Error, disconnected from "${this.#url}"`);
            this.dispatch("close", { error: true });
          });
          ws.on("close", () => {
            this.disconnect(ws);
            this.log(`Disconnected from "${this.#url}"`);
            this.dispatch("close", { error: false });
          });
          this.#ws = ws;
          resolve(true);
        });
      });
    }
  }

  disconnect(ws?: WebSocket) {
    if (ws) {
      ws.close();
    } else if (this.#ws) {
      this.#ws.close();
    }

    this.#ws = null;
    return true;
  }

  /**
   * Receives an event from WebSocket and dispatches as "server.{eventName}" and "server.*" events
   * @param {Message} message
   * @returns {true}
   */
  receive(message: Record<string, unknown>): true {
    this.log(`received:`, message);
    if (message.response_type == ChatResponseType.End) {
      this.dispatch("server.response.end", message);
      this.#isNewMessage = true;
    } else if (message.response_type == ChatResponseType.Error) {
      this.dispatch("server.response.error", message);
      this.#isNewMessage = true;
    } else if (this.#isNewMessage) {
      this.dispatch("server.response.start", message);
      this.#isNewMessage = false;
    } else {
      this.dispatch(`server.response.delta`, message);
    }
    return true;
  }

  /**
   * @param {string} data
   * @returns {true}
   */
  send(data: string): true {
    if (!this.isConnected()) {
      throw new Error(`Is NOT connected`);
    }

    this.log(`sent:`, data);
    this.#ws?.send(data);
    return true;
  }
}
