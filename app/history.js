// Undo and redo over a sequence of immutable states.

export class History {
  constructor(state, limit = 200) {
    this.past = [];
    this.future = [];
    this.present = state;
    this.limit = limit;
  }

  push(state) {
    if (state === this.present) return;
    this.past.push(this.present);
    if (this.past.length > this.limit) this.past.shift();
    this.present = state;
    this.future = [];
  }

  undo() {
    if (!this.past.length) return false;
    this.future.push(this.present);
    this.present = this.past.pop();
    return true;
  }

  redo() {
    if (!this.future.length) return false;
    this.past.push(this.present);
    this.present = this.future.pop();
    return true;
  }
}
