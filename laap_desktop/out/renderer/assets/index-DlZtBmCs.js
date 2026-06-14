function getDefaultExportFromCjs(x2) {
  return x2 && x2.__esModule && Object.prototype.hasOwnProperty.call(x2, "default") ? x2["default"] : x2;
}
var jsxRuntime = { exports: {} };
var reactJsxRuntime_production_min = {};
var react = { exports: {} };
var react_production_min = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var l$1 = Symbol.for("react.element"), n$1 = Symbol.for("react.portal"), p$2 = Symbol.for("react.fragment"), q$2 = Symbol.for("react.strict_mode"), r = Symbol.for("react.profiler"), t = Symbol.for("react.provider"), u = Symbol.for("react.context"), v$2 = Symbol.for("react.forward_ref"), w$1 = Symbol.for("react.suspense"), x$1 = Symbol.for("react.memo"), y$1 = Symbol.for("react.lazy"), z$2 = Symbol.iterator;
function A$2(a) {
  if (null === a || "object" !== typeof a) return null;
  a = z$2 && a[z$2] || a["@@iterator"];
  return "function" === typeof a ? a : null;
}
var B$2 = { isMounted: function() {
  return false;
}, enqueueForceUpdate: function() {
}, enqueueReplaceState: function() {
}, enqueueSetState: function() {
} }, C$1 = Object.assign, D$2 = {};
function E$2(a, b2, e) {
  this.props = a;
  this.context = b2;
  this.refs = D$2;
  this.updater = e || B$2;
}
E$2.prototype.isReactComponent = {};
E$2.prototype.setState = function(a, b2) {
  if ("object" !== typeof a && "function" !== typeof a && null != a) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
  this.updater.enqueueSetState(this, a, b2, "setState");
};
E$2.prototype.forceUpdate = function(a) {
  this.updater.enqueueForceUpdate(this, a, "forceUpdate");
};
function F$1() {
}
F$1.prototype = E$2.prototype;
function G$1(a, b2, e) {
  this.props = a;
  this.context = b2;
  this.refs = D$2;
  this.updater = e || B$2;
}
var H$2 = G$1.prototype = new F$1();
H$2.constructor = G$1;
C$1(H$2, E$2.prototype);
H$2.isPureReactComponent = true;
var I$2 = Array.isArray, J$1 = Object.prototype.hasOwnProperty, K$2 = { current: null }, L$2 = { key: true, ref: true, __self: true, __source: true };
function M$2(a, b2, e) {
  var d2, c = {}, k2 = null, h = null;
  if (null != b2) for (d2 in void 0 !== b2.ref && (h = b2.ref), void 0 !== b2.key && (k2 = "" + b2.key), b2) J$1.call(b2, d2) && !L$2.hasOwnProperty(d2) && (c[d2] = b2[d2]);
  var g2 = arguments.length - 2;
  if (1 === g2) c.children = e;
  else if (1 < g2) {
    for (var f2 = Array(g2), m2 = 0; m2 < g2; m2++) f2[m2] = arguments[m2 + 2];
    c.children = f2;
  }
  if (a && a.defaultProps) for (d2 in g2 = a.defaultProps, g2) void 0 === c[d2] && (c[d2] = g2[d2]);
  return { $$typeof: l$1, type: a, key: k2, ref: h, props: c, _owner: K$2.current };
}
function N$2(a, b2) {
  return { $$typeof: l$1, type: a.type, key: b2, ref: a.ref, props: a.props, _owner: a._owner };
}
function O$2(a) {
  return "object" === typeof a && null !== a && a.$$typeof === l$1;
}
function escape(a) {
  var b2 = { "=": "=0", ":": "=2" };
  return "$" + a.replace(/[=:]/g, function(a2) {
    return b2[a2];
  });
}
var P$2 = /\/+/g;
function Q$2(a, b2) {
  return "object" === typeof a && null !== a && null != a.key ? escape("" + a.key) : b2.toString(36);
}
function R$1(a, b2, e, d2, c) {
  var k2 = typeof a;
  if ("undefined" === k2 || "boolean" === k2) a = null;
  var h = false;
  if (null === a) h = true;
  else switch (k2) {
    case "string":
    case "number":
      h = true;
      break;
    case "object":
      switch (a.$$typeof) {
        case l$1:
        case n$1:
          h = true;
      }
  }
  if (h) return h = a, c = c(h), a = "" === d2 ? "." + Q$2(h, 0) : d2, I$2(c) ? (e = "", null != a && (e = a.replace(P$2, "$&/") + "/"), R$1(c, b2, e, "", function(a2) {
    return a2;
  })) : null != c && (O$2(c) && (c = N$2(c, e + (!c.key || h && h.key === c.key ? "" : ("" + c.key).replace(P$2, "$&/") + "/") + a)), b2.push(c)), 1;
  h = 0;
  d2 = "" === d2 ? "." : d2 + ":";
  if (I$2(a)) for (var g2 = 0; g2 < a.length; g2++) {
    k2 = a[g2];
    var f2 = d2 + Q$2(k2, g2);
    h += R$1(k2, b2, e, f2, c);
  }
  else if (f2 = A$2(a), "function" === typeof f2) for (a = f2.call(a), g2 = 0; !(k2 = a.next()).done; ) k2 = k2.value, f2 = d2 + Q$2(k2, g2++), h += R$1(k2, b2, e, f2, c);
  else if ("object" === k2) throw b2 = String(a), Error("Objects are not valid as a React child (found: " + ("[object Object]" === b2 ? "object with keys {" + Object.keys(a).join(", ") + "}" : b2) + "). If you meant to render a collection of children, use an array instead.");
  return h;
}
function S$1(a, b2, e) {
  if (null == a) return a;
  var d2 = [], c = 0;
  R$1(a, d2, "", "", function(a2) {
    return b2.call(e, a2, c++);
  });
  return d2;
}
function T$2(a) {
  if (-1 === a._status) {
    var b2 = a._result;
    b2 = b2();
    b2.then(function(b3) {
      if (0 === a._status || -1 === a._status) a._status = 1, a._result = b3;
    }, function(b3) {
      if (0 === a._status || -1 === a._status) a._status = 2, a._result = b3;
    });
    -1 === a._status && (a._status = 0, a._result = b2);
  }
  if (1 === a._status) return a._result.default;
  throw a._result;
}
var U$2 = { current: null }, V$2 = { transition: null }, W$2 = { ReactCurrentDispatcher: U$2, ReactCurrentBatchConfig: V$2, ReactCurrentOwner: K$2 };
function X$2() {
  throw Error("act(...) is not supported in production builds of React.");
}
react_production_min.Children = { map: S$1, forEach: function(a, b2, e) {
  S$1(a, function() {
    b2.apply(this, arguments);
  }, e);
}, count: function(a) {
  var b2 = 0;
  S$1(a, function() {
    b2++;
  });
  return b2;
}, toArray: function(a) {
  return S$1(a, function(a2) {
    return a2;
  }) || [];
}, only: function(a) {
  if (!O$2(a)) throw Error("React.Children.only expected to receive a single React element child.");
  return a;
} };
react_production_min.Component = E$2;
react_production_min.Fragment = p$2;
react_production_min.Profiler = r;
react_production_min.PureComponent = G$1;
react_production_min.StrictMode = q$2;
react_production_min.Suspense = w$1;
react_production_min.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = W$2;
react_production_min.act = X$2;
react_production_min.cloneElement = function(a, b2, e) {
  if (null === a || void 0 === a) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + a + ".");
  var d2 = C$1({}, a.props), c = a.key, k2 = a.ref, h = a._owner;
  if (null != b2) {
    void 0 !== b2.ref && (k2 = b2.ref, h = K$2.current);
    void 0 !== b2.key && (c = "" + b2.key);
    if (a.type && a.type.defaultProps) var g2 = a.type.defaultProps;
    for (f2 in b2) J$1.call(b2, f2) && !L$2.hasOwnProperty(f2) && (d2[f2] = void 0 === b2[f2] && void 0 !== g2 ? g2[f2] : b2[f2]);
  }
  var f2 = arguments.length - 2;
  if (1 === f2) d2.children = e;
  else if (1 < f2) {
    g2 = Array(f2);
    for (var m2 = 0; m2 < f2; m2++) g2[m2] = arguments[m2 + 2];
    d2.children = g2;
  }
  return { $$typeof: l$1, type: a.type, key: c, ref: k2, props: d2, _owner: h };
};
react_production_min.createContext = function(a) {
  a = { $$typeof: u, _currentValue: a, _currentValue2: a, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null };
  a.Provider = { $$typeof: t, _context: a };
  return a.Consumer = a;
};
react_production_min.createElement = M$2;
react_production_min.createFactory = function(a) {
  var b2 = M$2.bind(null, a);
  b2.type = a;
  return b2;
};
react_production_min.createRef = function() {
  return { current: null };
};
react_production_min.forwardRef = function(a) {
  return { $$typeof: v$2, render: a };
};
react_production_min.isValidElement = O$2;
react_production_min.lazy = function(a) {
  return { $$typeof: y$1, _payload: { _status: -1, _result: a }, _init: T$2 };
};
react_production_min.memo = function(a, b2) {
  return { $$typeof: x$1, type: a, compare: void 0 === b2 ? null : b2 };
};
react_production_min.startTransition = function(a) {
  var b2 = V$2.transition;
  V$2.transition = {};
  try {
    a();
  } finally {
    V$2.transition = b2;
  }
};
react_production_min.unstable_act = X$2;
react_production_min.useCallback = function(a, b2) {
  return U$2.current.useCallback(a, b2);
};
react_production_min.useContext = function(a) {
  return U$2.current.useContext(a);
};
react_production_min.useDebugValue = function() {
};
react_production_min.useDeferredValue = function(a) {
  return U$2.current.useDeferredValue(a);
};
react_production_min.useEffect = function(a, b2) {
  return U$2.current.useEffect(a, b2);
};
react_production_min.useId = function() {
  return U$2.current.useId();
};
react_production_min.useImperativeHandle = function(a, b2, e) {
  return U$2.current.useImperativeHandle(a, b2, e);
};
react_production_min.useInsertionEffect = function(a, b2) {
  return U$2.current.useInsertionEffect(a, b2);
};
react_production_min.useLayoutEffect = function(a, b2) {
  return U$2.current.useLayoutEffect(a, b2);
};
react_production_min.useMemo = function(a, b2) {
  return U$2.current.useMemo(a, b2);
};
react_production_min.useReducer = function(a, b2, e) {
  return U$2.current.useReducer(a, b2, e);
};
react_production_min.useRef = function(a) {
  return U$2.current.useRef(a);
};
react_production_min.useState = function(a) {
  return U$2.current.useState(a);
};
react_production_min.useSyncExternalStore = function(a, b2, e) {
  return U$2.current.useSyncExternalStore(a, b2, e);
};
react_production_min.useTransition = function() {
  return U$2.current.useTransition();
};
react_production_min.version = "18.3.1";
{
  react.exports = react_production_min;
}
var reactExports = react.exports;
const React = /* @__PURE__ */ getDefaultExportFromCjs(reactExports);
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var f = reactExports, k = Symbol.for("react.element"), l = Symbol.for("react.fragment"), m$2 = Object.prototype.hasOwnProperty, n = f.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, p$1 = { key: true, ref: true, __self: true, __source: true };
function q$1(c, a, g2) {
  var b2, d2 = {}, e = null, h = null;
  void 0 !== g2 && (e = "" + g2);
  void 0 !== a.key && (e = "" + a.key);
  void 0 !== a.ref && (h = a.ref);
  for (b2 in a) m$2.call(a, b2) && !p$1.hasOwnProperty(b2) && (d2[b2] = a[b2]);
  if (c && c.defaultProps) for (b2 in a = c.defaultProps, a) void 0 === d2[b2] && (d2[b2] = a[b2]);
  return { $$typeof: k, type: c, key: e, ref: h, props: d2, _owner: n.current };
}
reactJsxRuntime_production_min.Fragment = l;
reactJsxRuntime_production_min.jsx = q$1;
reactJsxRuntime_production_min.jsxs = q$1;
{
  jsxRuntime.exports = reactJsxRuntime_production_min;
}
var jsxRuntimeExports = jsxRuntime.exports;
var client = {};
var reactDom = { exports: {} };
var reactDom_production_min = {};
var scheduler = { exports: {} };
var scheduler_production_min = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function(exports) {
  function f2(a, b2) {
    var c = a.length;
    a.push(b2);
    a: for (; 0 < c; ) {
      var d2 = c - 1 >>> 1, e = a[d2];
      if (0 < g2(e, b2)) a[d2] = b2, a[c] = e, c = d2;
      else break a;
    }
  }
  function h(a) {
    return 0 === a.length ? null : a[0];
  }
  function k2(a) {
    if (0 === a.length) return null;
    var b2 = a[0], c = a.pop();
    if (c !== b2) {
      a[0] = c;
      a: for (var d2 = 0, e = a.length, w2 = e >>> 1; d2 < w2; ) {
        var m2 = 2 * (d2 + 1) - 1, C2 = a[m2], n2 = m2 + 1, x2 = a[n2];
        if (0 > g2(C2, c)) n2 < e && 0 > g2(x2, C2) ? (a[d2] = x2, a[n2] = c, d2 = n2) : (a[d2] = C2, a[m2] = c, d2 = m2);
        else if (n2 < e && 0 > g2(x2, c)) a[d2] = x2, a[n2] = c, d2 = n2;
        else break a;
      }
    }
    return b2;
  }
  function g2(a, b2) {
    var c = a.sortIndex - b2.sortIndex;
    return 0 !== c ? c : a.id - b2.id;
  }
  if ("object" === typeof performance && "function" === typeof performance.now) {
    var l4 = performance;
    exports.unstable_now = function() {
      return l4.now();
    };
  } else {
    var p2 = Date, q2 = p2.now();
    exports.unstable_now = function() {
      return p2.now() - q2;
    };
  }
  var r2 = [], t2 = [], u2 = 1, v2 = null, y2 = 3, z2 = false, A2 = false, B2 = false, D2 = "function" === typeof setTimeout ? setTimeout : null, E2 = "function" === typeof clearTimeout ? clearTimeout : null, F2 = "undefined" !== typeof setImmediate ? setImmediate : null;
  "undefined" !== typeof navigator && void 0 !== navigator.scheduling && void 0 !== navigator.scheduling.isInputPending && navigator.scheduling.isInputPending.bind(navigator.scheduling);
  function G2(a) {
    for (var b2 = h(t2); null !== b2; ) {
      if (null === b2.callback) k2(t2);
      else if (b2.startTime <= a) k2(t2), b2.sortIndex = b2.expirationTime, f2(r2, b2);
      else break;
      b2 = h(t2);
    }
  }
  function H2(a) {
    B2 = false;
    G2(a);
    if (!A2) if (null !== h(r2)) A2 = true, I2(J2);
    else {
      var b2 = h(t2);
      null !== b2 && K2(H2, b2.startTime - a);
    }
  }
  function J2(a, b2) {
    A2 = false;
    B2 && (B2 = false, E2(L2), L2 = -1);
    z2 = true;
    var c = y2;
    try {
      G2(b2);
      for (v2 = h(r2); null !== v2 && (!(v2.expirationTime > b2) || a && !M2()); ) {
        var d2 = v2.callback;
        if ("function" === typeof d2) {
          v2.callback = null;
          y2 = v2.priorityLevel;
          var e = d2(v2.expirationTime <= b2);
          b2 = exports.unstable_now();
          "function" === typeof e ? v2.callback = e : v2 === h(r2) && k2(r2);
          G2(b2);
        } else k2(r2);
        v2 = h(r2);
      }
      if (null !== v2) var w2 = true;
      else {
        var m2 = h(t2);
        null !== m2 && K2(H2, m2.startTime - b2);
        w2 = false;
      }
      return w2;
    } finally {
      v2 = null, y2 = c, z2 = false;
    }
  }
  var N2 = false, O2 = null, L2 = -1, P2 = 5, Q2 = -1;
  function M2() {
    return exports.unstable_now() - Q2 < P2 ? false : true;
  }
  function R2() {
    if (null !== O2) {
      var a = exports.unstable_now();
      Q2 = a;
      var b2 = true;
      try {
        b2 = O2(true, a);
      } finally {
        b2 ? S2() : (N2 = false, O2 = null);
      }
    } else N2 = false;
  }
  var S2;
  if ("function" === typeof F2) S2 = function() {
    F2(R2);
  };
  else if ("undefined" !== typeof MessageChannel) {
    var T2 = new MessageChannel(), U2 = T2.port2;
    T2.port1.onmessage = R2;
    S2 = function() {
      U2.postMessage(null);
    };
  } else S2 = function() {
    D2(R2, 0);
  };
  function I2(a) {
    O2 = a;
    N2 || (N2 = true, S2());
  }
  function K2(a, b2) {
    L2 = D2(function() {
      a(exports.unstable_now());
    }, b2);
  }
  exports.unstable_IdlePriority = 5;
  exports.unstable_ImmediatePriority = 1;
  exports.unstable_LowPriority = 4;
  exports.unstable_NormalPriority = 3;
  exports.unstable_Profiling = null;
  exports.unstable_UserBlockingPriority = 2;
  exports.unstable_cancelCallback = function(a) {
    a.callback = null;
  };
  exports.unstable_continueExecution = function() {
    A2 || z2 || (A2 = true, I2(J2));
  };
  exports.unstable_forceFrameRate = function(a) {
    0 > a || 125 < a ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : P2 = 0 < a ? Math.floor(1e3 / a) : 5;
  };
  exports.unstable_getCurrentPriorityLevel = function() {
    return y2;
  };
  exports.unstable_getFirstCallbackNode = function() {
    return h(r2);
  };
  exports.unstable_next = function(a) {
    switch (y2) {
      case 1:
      case 2:
      case 3:
        var b2 = 3;
        break;
      default:
        b2 = y2;
    }
    var c = y2;
    y2 = b2;
    try {
      return a();
    } finally {
      y2 = c;
    }
  };
  exports.unstable_pauseExecution = function() {
  };
  exports.unstable_requestPaint = function() {
  };
  exports.unstable_runWithPriority = function(a, b2) {
    switch (a) {
      case 1:
      case 2:
      case 3:
      case 4:
      case 5:
        break;
      default:
        a = 3;
    }
    var c = y2;
    y2 = a;
    try {
      return b2();
    } finally {
      y2 = c;
    }
  };
  exports.unstable_scheduleCallback = function(a, b2, c) {
    var d2 = exports.unstable_now();
    "object" === typeof c && null !== c ? (c = c.delay, c = "number" === typeof c && 0 < c ? d2 + c : d2) : c = d2;
    switch (a) {
      case 1:
        var e = -1;
        break;
      case 2:
        e = 250;
        break;
      case 5:
        e = 1073741823;
        break;
      case 4:
        e = 1e4;
        break;
      default:
        e = 5e3;
    }
    e = c + e;
    a = { id: u2++, callback: b2, priorityLevel: a, startTime: c, expirationTime: e, sortIndex: -1 };
    c > d2 ? (a.sortIndex = c, f2(t2, a), null === h(r2) && a === h(t2) && (B2 ? (E2(L2), L2 = -1) : B2 = true, K2(H2, c - d2))) : (a.sortIndex = e, f2(r2, a), A2 || z2 || (A2 = true, I2(J2)));
    return a;
  };
  exports.unstable_shouldYield = M2;
  exports.unstable_wrapCallback = function(a) {
    var b2 = y2;
    return function() {
      var c = y2;
      y2 = b2;
      try {
        return a.apply(this, arguments);
      } finally {
        y2 = c;
      }
    };
  };
})(scheduler_production_min);
{
  scheduler.exports = scheduler_production_min;
}
var schedulerExports = scheduler.exports;
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var aa = reactExports, ca = schedulerExports;
function p(a) {
  for (var b2 = "https://reactjs.org/docs/error-decoder.html?invariant=" + a, c = 1; c < arguments.length; c++) b2 += "&args[]=" + encodeURIComponent(arguments[c]);
  return "Minified React error #" + a + "; visit " + b2 + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
}
var da = /* @__PURE__ */ new Set(), ea = {};
function fa(a, b2) {
  ha(a, b2);
  ha(a + "Capture", b2);
}
function ha(a, b2) {
  ea[a] = b2;
  for (a = 0; a < b2.length; a++) da.add(b2[a]);
}
var ia = !("undefined" === typeof window || "undefined" === typeof window.document || "undefined" === typeof window.document.createElement), ja = Object.prototype.hasOwnProperty, ka = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, la = {}, ma = {};
function oa(a) {
  if (ja.call(ma, a)) return true;
  if (ja.call(la, a)) return false;
  if (ka.test(a)) return ma[a] = true;
  la[a] = true;
  return false;
}
function pa(a, b2, c, d2) {
  if (null !== c && 0 === c.type) return false;
  switch (typeof b2) {
    case "function":
    case "symbol":
      return true;
    case "boolean":
      if (d2) return false;
      if (null !== c) return !c.acceptsBooleans;
      a = a.toLowerCase().slice(0, 5);
      return "data-" !== a && "aria-" !== a;
    default:
      return false;
  }
}
function qa(a, b2, c, d2) {
  if (null === b2 || "undefined" === typeof b2 || pa(a, b2, c, d2)) return true;
  if (d2) return false;
  if (null !== c) switch (c.type) {
    case 3:
      return !b2;
    case 4:
      return false === b2;
    case 5:
      return isNaN(b2);
    case 6:
      return isNaN(b2) || 1 > b2;
  }
  return false;
}
function v$1(a, b2, c, d2, e, f2, g2) {
  this.acceptsBooleans = 2 === b2 || 3 === b2 || 4 === b2;
  this.attributeName = d2;
  this.attributeNamespace = e;
  this.mustUseProperty = c;
  this.propertyName = a;
  this.type = b2;
  this.sanitizeURL = f2;
  this.removeEmptyString = g2;
}
var z$1 = {};
"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(a) {
  z$1[a] = new v$1(a, 0, false, a, null, false, false);
});
[["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(a) {
  var b2 = a[0];
  z$1[b2] = new v$1(b2, 1, false, a[1], null, false, false);
});
["contentEditable", "draggable", "spellCheck", "value"].forEach(function(a) {
  z$1[a] = new v$1(a, 2, false, a.toLowerCase(), null, false, false);
});
["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(a) {
  z$1[a] = new v$1(a, 2, false, a, null, false, false);
});
"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(a) {
  z$1[a] = new v$1(a, 3, false, a.toLowerCase(), null, false, false);
});
["checked", "multiple", "muted", "selected"].forEach(function(a) {
  z$1[a] = new v$1(a, 3, true, a, null, false, false);
});
["capture", "download"].forEach(function(a) {
  z$1[a] = new v$1(a, 4, false, a, null, false, false);
});
["cols", "rows", "size", "span"].forEach(function(a) {
  z$1[a] = new v$1(a, 6, false, a, null, false, false);
});
["rowSpan", "start"].forEach(function(a) {
  z$1[a] = new v$1(a, 5, false, a.toLowerCase(), null, false, false);
});
var ra = /[\-:]([a-z])/g;
function sa(a) {
  return a[1].toUpperCase();
}
"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(a) {
  var b2 = a.replace(
    ra,
    sa
  );
  z$1[b2] = new v$1(b2, 1, false, a, null, false, false);
});
"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(a) {
  var b2 = a.replace(ra, sa);
  z$1[b2] = new v$1(b2, 1, false, a, "http://www.w3.org/1999/xlink", false, false);
});
["xml:base", "xml:lang", "xml:space"].forEach(function(a) {
  var b2 = a.replace(ra, sa);
  z$1[b2] = new v$1(b2, 1, false, a, "http://www.w3.org/XML/1998/namespace", false, false);
});
["tabIndex", "crossOrigin"].forEach(function(a) {
  z$1[a] = new v$1(a, 1, false, a.toLowerCase(), null, false, false);
});
z$1.xlinkHref = new v$1("xlinkHref", 1, false, "xlink:href", "http://www.w3.org/1999/xlink", true, false);
["src", "href", "action", "formAction"].forEach(function(a) {
  z$1[a] = new v$1(a, 1, false, a.toLowerCase(), null, true, true);
});
function ta(a, b2, c, d2) {
  var e = z$1.hasOwnProperty(b2) ? z$1[b2] : null;
  if (null !== e ? 0 !== e.type : d2 || !(2 < b2.length) || "o" !== b2[0] && "O" !== b2[0] || "n" !== b2[1] && "N" !== b2[1]) qa(b2, c, e, d2) && (c = null), d2 || null === e ? oa(b2) && (null === c ? a.removeAttribute(b2) : a.setAttribute(b2, "" + c)) : e.mustUseProperty ? a[e.propertyName] = null === c ? 3 === e.type ? false : "" : c : (b2 = e.attributeName, d2 = e.attributeNamespace, null === c ? a.removeAttribute(b2) : (e = e.type, c = 3 === e || 4 === e && true === c ? "" : "" + c, d2 ? a.setAttributeNS(d2, b2, c) : a.setAttribute(b2, c)));
}
var ua = aa.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, va = Symbol.for("react.element"), wa = Symbol.for("react.portal"), ya = Symbol.for("react.fragment"), za = Symbol.for("react.strict_mode"), Aa = Symbol.for("react.profiler"), Ba = Symbol.for("react.provider"), Ca = Symbol.for("react.context"), Da = Symbol.for("react.forward_ref"), Ea = Symbol.for("react.suspense"), Fa = Symbol.for("react.suspense_list"), Ga = Symbol.for("react.memo"), Ha = Symbol.for("react.lazy");
var Ia = Symbol.for("react.offscreen");
var Ja = Symbol.iterator;
function Ka(a) {
  if (null === a || "object" !== typeof a) return null;
  a = Ja && a[Ja] || a["@@iterator"];
  return "function" === typeof a ? a : null;
}
var A$1 = Object.assign, La;
function Ma(a) {
  if (void 0 === La) try {
    throw Error();
  } catch (c) {
    var b2 = c.stack.trim().match(/\n( *(at )?)/);
    La = b2 && b2[1] || "";
  }
  return "\n" + La + a;
}
var Na = false;
function Oa(a, b2) {
  if (!a || Na) return "";
  Na = true;
  var c = Error.prepareStackTrace;
  Error.prepareStackTrace = void 0;
  try {
    if (b2) if (b2 = function() {
      throw Error();
    }, Object.defineProperty(b2.prototype, "props", { set: function() {
      throw Error();
    } }), "object" === typeof Reflect && Reflect.construct) {
      try {
        Reflect.construct(b2, []);
      } catch (l4) {
        var d2 = l4;
      }
      Reflect.construct(a, [], b2);
    } else {
      try {
        b2.call();
      } catch (l4) {
        d2 = l4;
      }
      a.call(b2.prototype);
    }
    else {
      try {
        throw Error();
      } catch (l4) {
        d2 = l4;
      }
      a();
    }
  } catch (l4) {
    if (l4 && d2 && "string" === typeof l4.stack) {
      for (var e = l4.stack.split("\n"), f2 = d2.stack.split("\n"), g2 = e.length - 1, h = f2.length - 1; 1 <= g2 && 0 <= h && e[g2] !== f2[h]; ) h--;
      for (; 1 <= g2 && 0 <= h; g2--, h--) if (e[g2] !== f2[h]) {
        if (1 !== g2 || 1 !== h) {
          do
            if (g2--, h--, 0 > h || e[g2] !== f2[h]) {
              var k2 = "\n" + e[g2].replace(" at new ", " at ");
              a.displayName && k2.includes("<anonymous>") && (k2 = k2.replace("<anonymous>", a.displayName));
              return k2;
            }
          while (1 <= g2 && 0 <= h);
        }
        break;
      }
    }
  } finally {
    Na = false, Error.prepareStackTrace = c;
  }
  return (a = a ? a.displayName || a.name : "") ? Ma(a) : "";
}
function Pa(a) {
  switch (a.tag) {
    case 5:
      return Ma(a.type);
    case 16:
      return Ma("Lazy");
    case 13:
      return Ma("Suspense");
    case 19:
      return Ma("SuspenseList");
    case 0:
    case 2:
    case 15:
      return a = Oa(a.type, false), a;
    case 11:
      return a = Oa(a.type.render, false), a;
    case 1:
      return a = Oa(a.type, true), a;
    default:
      return "";
  }
}
function Qa(a) {
  if (null == a) return null;
  if ("function" === typeof a) return a.displayName || a.name || null;
  if ("string" === typeof a) return a;
  switch (a) {
    case ya:
      return "Fragment";
    case wa:
      return "Portal";
    case Aa:
      return "Profiler";
    case za:
      return "StrictMode";
    case Ea:
      return "Suspense";
    case Fa:
      return "SuspenseList";
  }
  if ("object" === typeof a) switch (a.$$typeof) {
    case Ca:
      return (a.displayName || "Context") + ".Consumer";
    case Ba:
      return (a._context.displayName || "Context") + ".Provider";
    case Da:
      var b2 = a.render;
      a = a.displayName;
      a || (a = b2.displayName || b2.name || "", a = "" !== a ? "ForwardRef(" + a + ")" : "ForwardRef");
      return a;
    case Ga:
      return b2 = a.displayName || null, null !== b2 ? b2 : Qa(a.type) || "Memo";
    case Ha:
      b2 = a._payload;
      a = a._init;
      try {
        return Qa(a(b2));
      } catch (c) {
      }
  }
  return null;
}
function Ra(a) {
  var b2 = a.type;
  switch (a.tag) {
    case 24:
      return "Cache";
    case 9:
      return (b2.displayName || "Context") + ".Consumer";
    case 10:
      return (b2._context.displayName || "Context") + ".Provider";
    case 18:
      return "DehydratedFragment";
    case 11:
      return a = b2.render, a = a.displayName || a.name || "", b2.displayName || ("" !== a ? "ForwardRef(" + a + ")" : "ForwardRef");
    case 7:
      return "Fragment";
    case 5:
      return b2;
    case 4:
      return "Portal";
    case 3:
      return "Root";
    case 6:
      return "Text";
    case 16:
      return Qa(b2);
    case 8:
      return b2 === za ? "StrictMode" : "Mode";
    case 22:
      return "Offscreen";
    case 12:
      return "Profiler";
    case 21:
      return "Scope";
    case 13:
      return "Suspense";
    case 19:
      return "SuspenseList";
    case 25:
      return "TracingMarker";
    case 1:
    case 0:
    case 17:
    case 2:
    case 14:
    case 15:
      if ("function" === typeof b2) return b2.displayName || b2.name || null;
      if ("string" === typeof b2) return b2;
  }
  return null;
}
function Sa(a) {
  switch (typeof a) {
    case "boolean":
    case "number":
    case "string":
    case "undefined":
      return a;
    case "object":
      return a;
    default:
      return "";
  }
}
function Ta(a) {
  var b2 = a.type;
  return (a = a.nodeName) && "input" === a.toLowerCase() && ("checkbox" === b2 || "radio" === b2);
}
function Ua(a) {
  var b2 = Ta(a) ? "checked" : "value", c = Object.getOwnPropertyDescriptor(a.constructor.prototype, b2), d2 = "" + a[b2];
  if (!a.hasOwnProperty(b2) && "undefined" !== typeof c && "function" === typeof c.get && "function" === typeof c.set) {
    var e = c.get, f2 = c.set;
    Object.defineProperty(a, b2, { configurable: true, get: function() {
      return e.call(this);
    }, set: function(a2) {
      d2 = "" + a2;
      f2.call(this, a2);
    } });
    Object.defineProperty(a, b2, { enumerable: c.enumerable });
    return { getValue: function() {
      return d2;
    }, setValue: function(a2) {
      d2 = "" + a2;
    }, stopTracking: function() {
      a._valueTracker = null;
      delete a[b2];
    } };
  }
}
function Va(a) {
  a._valueTracker || (a._valueTracker = Ua(a));
}
function Wa(a) {
  if (!a) return false;
  var b2 = a._valueTracker;
  if (!b2) return true;
  var c = b2.getValue();
  var d2 = "";
  a && (d2 = Ta(a) ? a.checked ? "true" : "false" : a.value);
  a = d2;
  return a !== c ? (b2.setValue(a), true) : false;
}
function Xa(a) {
  a = a || ("undefined" !== typeof document ? document : void 0);
  if ("undefined" === typeof a) return null;
  try {
    return a.activeElement || a.body;
  } catch (b2) {
    return a.body;
  }
}
function Ya(a, b2) {
  var c = b2.checked;
  return A$1({}, b2, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: null != c ? c : a._wrapperState.initialChecked });
}
function Za(a, b2) {
  var c = null == b2.defaultValue ? "" : b2.defaultValue, d2 = null != b2.checked ? b2.checked : b2.defaultChecked;
  c = Sa(null != b2.value ? b2.value : c);
  a._wrapperState = { initialChecked: d2, initialValue: c, controlled: "checkbox" === b2.type || "radio" === b2.type ? null != b2.checked : null != b2.value };
}
function ab(a, b2) {
  b2 = b2.checked;
  null != b2 && ta(a, "checked", b2, false);
}
function bb(a, b2) {
  ab(a, b2);
  var c = Sa(b2.value), d2 = b2.type;
  if (null != c) if ("number" === d2) {
    if (0 === c && "" === a.value || a.value != c) a.value = "" + c;
  } else a.value !== "" + c && (a.value = "" + c);
  else if ("submit" === d2 || "reset" === d2) {
    a.removeAttribute("value");
    return;
  }
  b2.hasOwnProperty("value") ? cb(a, b2.type, c) : b2.hasOwnProperty("defaultValue") && cb(a, b2.type, Sa(b2.defaultValue));
  null == b2.checked && null != b2.defaultChecked && (a.defaultChecked = !!b2.defaultChecked);
}
function db(a, b2, c) {
  if (b2.hasOwnProperty("value") || b2.hasOwnProperty("defaultValue")) {
    var d2 = b2.type;
    if (!("submit" !== d2 && "reset" !== d2 || void 0 !== b2.value && null !== b2.value)) return;
    b2 = "" + a._wrapperState.initialValue;
    c || b2 === a.value || (a.value = b2);
    a.defaultValue = b2;
  }
  c = a.name;
  "" !== c && (a.name = "");
  a.defaultChecked = !!a._wrapperState.initialChecked;
  "" !== c && (a.name = c);
}
function cb(a, b2, c) {
  if ("number" !== b2 || Xa(a.ownerDocument) !== a) null == c ? a.defaultValue = "" + a._wrapperState.initialValue : a.defaultValue !== "" + c && (a.defaultValue = "" + c);
}
var eb = Array.isArray;
function fb(a, b2, c, d2) {
  a = a.options;
  if (b2) {
    b2 = {};
    for (var e = 0; e < c.length; e++) b2["$" + c[e]] = true;
    for (c = 0; c < a.length; c++) e = b2.hasOwnProperty("$" + a[c].value), a[c].selected !== e && (a[c].selected = e), e && d2 && (a[c].defaultSelected = true);
  } else {
    c = "" + Sa(c);
    b2 = null;
    for (e = 0; e < a.length; e++) {
      if (a[e].value === c) {
        a[e].selected = true;
        d2 && (a[e].defaultSelected = true);
        return;
      }
      null !== b2 || a[e].disabled || (b2 = a[e]);
    }
    null !== b2 && (b2.selected = true);
  }
}
function gb(a, b2) {
  if (null != b2.dangerouslySetInnerHTML) throw Error(p(91));
  return A$1({}, b2, { value: void 0, defaultValue: void 0, children: "" + a._wrapperState.initialValue });
}
function hb(a, b2) {
  var c = b2.value;
  if (null == c) {
    c = b2.children;
    b2 = b2.defaultValue;
    if (null != c) {
      if (null != b2) throw Error(p(92));
      if (eb(c)) {
        if (1 < c.length) throw Error(p(93));
        c = c[0];
      }
      b2 = c;
    }
    null == b2 && (b2 = "");
    c = b2;
  }
  a._wrapperState = { initialValue: Sa(c) };
}
function ib(a, b2) {
  var c = Sa(b2.value), d2 = Sa(b2.defaultValue);
  null != c && (c = "" + c, c !== a.value && (a.value = c), null == b2.defaultValue && a.defaultValue !== c && (a.defaultValue = c));
  null != d2 && (a.defaultValue = "" + d2);
}
function jb(a) {
  var b2 = a.textContent;
  b2 === a._wrapperState.initialValue && "" !== b2 && null !== b2 && (a.value = b2);
}
function kb(a) {
  switch (a) {
    case "svg":
      return "http://www.w3.org/2000/svg";
    case "math":
      return "http://www.w3.org/1998/Math/MathML";
    default:
      return "http://www.w3.org/1999/xhtml";
  }
}
function lb(a, b2) {
  return null == a || "http://www.w3.org/1999/xhtml" === a ? kb(b2) : "http://www.w3.org/2000/svg" === a && "foreignObject" === b2 ? "http://www.w3.org/1999/xhtml" : a;
}
var mb, nb = function(a) {
  return "undefined" !== typeof MSApp && MSApp.execUnsafeLocalFunction ? function(b2, c, d2, e) {
    MSApp.execUnsafeLocalFunction(function() {
      return a(b2, c, d2, e);
    });
  } : a;
}(function(a, b2) {
  if ("http://www.w3.org/2000/svg" !== a.namespaceURI || "innerHTML" in a) a.innerHTML = b2;
  else {
    mb = mb || document.createElement("div");
    mb.innerHTML = "<svg>" + b2.valueOf().toString() + "</svg>";
    for (b2 = mb.firstChild; a.firstChild; ) a.removeChild(a.firstChild);
    for (; b2.firstChild; ) a.appendChild(b2.firstChild);
  }
});
function ob(a, b2) {
  if (b2) {
    var c = a.firstChild;
    if (c && c === a.lastChild && 3 === c.nodeType) {
      c.nodeValue = b2;
      return;
    }
  }
  a.textContent = b2;
}
var pb = {
  animationIterationCount: true,
  aspectRatio: true,
  borderImageOutset: true,
  borderImageSlice: true,
  borderImageWidth: true,
  boxFlex: true,
  boxFlexGroup: true,
  boxOrdinalGroup: true,
  columnCount: true,
  columns: true,
  flex: true,
  flexGrow: true,
  flexPositive: true,
  flexShrink: true,
  flexNegative: true,
  flexOrder: true,
  gridArea: true,
  gridRow: true,
  gridRowEnd: true,
  gridRowSpan: true,
  gridRowStart: true,
  gridColumn: true,
  gridColumnEnd: true,
  gridColumnSpan: true,
  gridColumnStart: true,
  fontWeight: true,
  lineClamp: true,
  lineHeight: true,
  opacity: true,
  order: true,
  orphans: true,
  tabSize: true,
  widows: true,
  zIndex: true,
  zoom: true,
  fillOpacity: true,
  floodOpacity: true,
  stopOpacity: true,
  strokeDasharray: true,
  strokeDashoffset: true,
  strokeMiterlimit: true,
  strokeOpacity: true,
  strokeWidth: true
}, qb = ["Webkit", "ms", "Moz", "O"];
Object.keys(pb).forEach(function(a) {
  qb.forEach(function(b2) {
    b2 = b2 + a.charAt(0).toUpperCase() + a.substring(1);
    pb[b2] = pb[a];
  });
});
function rb(a, b2, c) {
  return null == b2 || "boolean" === typeof b2 || "" === b2 ? "" : c || "number" !== typeof b2 || 0 === b2 || pb.hasOwnProperty(a) && pb[a] ? ("" + b2).trim() : b2 + "px";
}
function sb(a, b2) {
  a = a.style;
  for (var c in b2) if (b2.hasOwnProperty(c)) {
    var d2 = 0 === c.indexOf("--"), e = rb(c, b2[c], d2);
    "float" === c && (c = "cssFloat");
    d2 ? a.setProperty(c, e) : a[c] = e;
  }
}
var tb = A$1({ menuitem: true }, { area: true, base: true, br: true, col: true, embed: true, hr: true, img: true, input: true, keygen: true, link: true, meta: true, param: true, source: true, track: true, wbr: true });
function ub(a, b2) {
  if (b2) {
    if (tb[a] && (null != b2.children || null != b2.dangerouslySetInnerHTML)) throw Error(p(137, a));
    if (null != b2.dangerouslySetInnerHTML) {
      if (null != b2.children) throw Error(p(60));
      if ("object" !== typeof b2.dangerouslySetInnerHTML || !("__html" in b2.dangerouslySetInnerHTML)) throw Error(p(61));
    }
    if (null != b2.style && "object" !== typeof b2.style) throw Error(p(62));
  }
}
function vb(a, b2) {
  if (-1 === a.indexOf("-")) return "string" === typeof b2.is;
  switch (a) {
    case "annotation-xml":
    case "color-profile":
    case "font-face":
    case "font-face-src":
    case "font-face-uri":
    case "font-face-format":
    case "font-face-name":
    case "missing-glyph":
      return false;
    default:
      return true;
  }
}
var wb = null;
function xb(a) {
  a = a.target || a.srcElement || window;
  a.correspondingUseElement && (a = a.correspondingUseElement);
  return 3 === a.nodeType ? a.parentNode : a;
}
var yb = null, zb = null, Ab = null;
function Bb(a) {
  if (a = Cb(a)) {
    if ("function" !== typeof yb) throw Error(p(280));
    var b2 = a.stateNode;
    b2 && (b2 = Db(b2), yb(a.stateNode, a.type, b2));
  }
}
function Eb(a) {
  zb ? Ab ? Ab.push(a) : Ab = [a] : zb = a;
}
function Fb() {
  if (zb) {
    var a = zb, b2 = Ab;
    Ab = zb = null;
    Bb(a);
    if (b2) for (a = 0; a < b2.length; a++) Bb(b2[a]);
  }
}
function Gb(a, b2) {
  return a(b2);
}
function Hb() {
}
var Ib = false;
function Jb(a, b2, c) {
  if (Ib) return a(b2, c);
  Ib = true;
  try {
    return Gb(a, b2, c);
  } finally {
    if (Ib = false, null !== zb || null !== Ab) Hb(), Fb();
  }
}
function Kb(a, b2) {
  var c = a.stateNode;
  if (null === c) return null;
  var d2 = Db(c);
  if (null === d2) return null;
  c = d2[b2];
  a: switch (b2) {
    case "onClick":
    case "onClickCapture":
    case "onDoubleClick":
    case "onDoubleClickCapture":
    case "onMouseDown":
    case "onMouseDownCapture":
    case "onMouseMove":
    case "onMouseMoveCapture":
    case "onMouseUp":
    case "onMouseUpCapture":
    case "onMouseEnter":
      (d2 = !d2.disabled) || (a = a.type, d2 = !("button" === a || "input" === a || "select" === a || "textarea" === a));
      a = !d2;
      break a;
    default:
      a = false;
  }
  if (a) return null;
  if (c && "function" !== typeof c) throw Error(p(231, b2, typeof c));
  return c;
}
var Lb = false;
if (ia) try {
  var Mb = {};
  Object.defineProperty(Mb, "passive", { get: function() {
    Lb = true;
  } });
  window.addEventListener("test", Mb, Mb);
  window.removeEventListener("test", Mb, Mb);
} catch (a) {
  Lb = false;
}
function Nb(a, b2, c, d2, e, f2, g2, h, k2) {
  var l4 = Array.prototype.slice.call(arguments, 3);
  try {
    b2.apply(c, l4);
  } catch (m2) {
    this.onError(m2);
  }
}
var Ob = false, Pb = null, Qb = false, Rb = null, Sb = { onError: function(a) {
  Ob = true;
  Pb = a;
} };
function Tb(a, b2, c, d2, e, f2, g2, h, k2) {
  Ob = false;
  Pb = null;
  Nb.apply(Sb, arguments);
}
function Ub(a, b2, c, d2, e, f2, g2, h, k2) {
  Tb.apply(this, arguments);
  if (Ob) {
    if (Ob) {
      var l4 = Pb;
      Ob = false;
      Pb = null;
    } else throw Error(p(198));
    Qb || (Qb = true, Rb = l4);
  }
}
function Vb(a) {
  var b2 = a, c = a;
  if (a.alternate) for (; b2.return; ) b2 = b2.return;
  else {
    a = b2;
    do
      b2 = a, 0 !== (b2.flags & 4098) && (c = b2.return), a = b2.return;
    while (a);
  }
  return 3 === b2.tag ? c : null;
}
function Wb(a) {
  if (13 === a.tag) {
    var b2 = a.memoizedState;
    null === b2 && (a = a.alternate, null !== a && (b2 = a.memoizedState));
    if (null !== b2) return b2.dehydrated;
  }
  return null;
}
function Xb(a) {
  if (Vb(a) !== a) throw Error(p(188));
}
function Yb(a) {
  var b2 = a.alternate;
  if (!b2) {
    b2 = Vb(a);
    if (null === b2) throw Error(p(188));
    return b2 !== a ? null : a;
  }
  for (var c = a, d2 = b2; ; ) {
    var e = c.return;
    if (null === e) break;
    var f2 = e.alternate;
    if (null === f2) {
      d2 = e.return;
      if (null !== d2) {
        c = d2;
        continue;
      }
      break;
    }
    if (e.child === f2.child) {
      for (f2 = e.child; f2; ) {
        if (f2 === c) return Xb(e), a;
        if (f2 === d2) return Xb(e), b2;
        f2 = f2.sibling;
      }
      throw Error(p(188));
    }
    if (c.return !== d2.return) c = e, d2 = f2;
    else {
      for (var g2 = false, h = e.child; h; ) {
        if (h === c) {
          g2 = true;
          c = e;
          d2 = f2;
          break;
        }
        if (h === d2) {
          g2 = true;
          d2 = e;
          c = f2;
          break;
        }
        h = h.sibling;
      }
      if (!g2) {
        for (h = f2.child; h; ) {
          if (h === c) {
            g2 = true;
            c = f2;
            d2 = e;
            break;
          }
          if (h === d2) {
            g2 = true;
            d2 = f2;
            c = e;
            break;
          }
          h = h.sibling;
        }
        if (!g2) throw Error(p(189));
      }
    }
    if (c.alternate !== d2) throw Error(p(190));
  }
  if (3 !== c.tag) throw Error(p(188));
  return c.stateNode.current === c ? a : b2;
}
function Zb(a) {
  a = Yb(a);
  return null !== a ? $b(a) : null;
}
function $b(a) {
  if (5 === a.tag || 6 === a.tag) return a;
  for (a = a.child; null !== a; ) {
    var b2 = $b(a);
    if (null !== b2) return b2;
    a = a.sibling;
  }
  return null;
}
var ac = ca.unstable_scheduleCallback, bc = ca.unstable_cancelCallback, cc = ca.unstable_shouldYield, dc = ca.unstable_requestPaint, B$1 = ca.unstable_now, ec = ca.unstable_getCurrentPriorityLevel, fc = ca.unstable_ImmediatePriority, gc = ca.unstable_UserBlockingPriority, hc = ca.unstable_NormalPriority, ic = ca.unstable_LowPriority, jc = ca.unstable_IdlePriority, kc = null, lc = null;
function mc(a) {
  if (lc && "function" === typeof lc.onCommitFiberRoot) try {
    lc.onCommitFiberRoot(kc, a, void 0, 128 === (a.current.flags & 128));
  } catch (b2) {
  }
}
var oc = Math.clz32 ? Math.clz32 : nc, pc = Math.log, qc = Math.LN2;
function nc(a) {
  a >>>= 0;
  return 0 === a ? 32 : 31 - (pc(a) / qc | 0) | 0;
}
var rc = 64, sc = 4194304;
function tc(a) {
  switch (a & -a) {
    case 1:
      return 1;
    case 2:
      return 2;
    case 4:
      return 4;
    case 8:
      return 8;
    case 16:
      return 16;
    case 32:
      return 32;
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return a & 4194240;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return a & 130023424;
    case 134217728:
      return 134217728;
    case 268435456:
      return 268435456;
    case 536870912:
      return 536870912;
    case 1073741824:
      return 1073741824;
    default:
      return a;
  }
}
function uc(a, b2) {
  var c = a.pendingLanes;
  if (0 === c) return 0;
  var d2 = 0, e = a.suspendedLanes, f2 = a.pingedLanes, g2 = c & 268435455;
  if (0 !== g2) {
    var h = g2 & ~e;
    0 !== h ? d2 = tc(h) : (f2 &= g2, 0 !== f2 && (d2 = tc(f2)));
  } else g2 = c & ~e, 0 !== g2 ? d2 = tc(g2) : 0 !== f2 && (d2 = tc(f2));
  if (0 === d2) return 0;
  if (0 !== b2 && b2 !== d2 && 0 === (b2 & e) && (e = d2 & -d2, f2 = b2 & -b2, e >= f2 || 16 === e && 0 !== (f2 & 4194240))) return b2;
  0 !== (d2 & 4) && (d2 |= c & 16);
  b2 = a.entangledLanes;
  if (0 !== b2) for (a = a.entanglements, b2 &= d2; 0 < b2; ) c = 31 - oc(b2), e = 1 << c, d2 |= a[c], b2 &= ~e;
  return d2;
}
function vc(a, b2) {
  switch (a) {
    case 1:
    case 2:
    case 4:
      return b2 + 250;
    case 8:
    case 16:
    case 32:
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return b2 + 5e3;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return -1;
    case 134217728:
    case 268435456:
    case 536870912:
    case 1073741824:
      return -1;
    default:
      return -1;
  }
}
function wc(a, b2) {
  for (var c = a.suspendedLanes, d2 = a.pingedLanes, e = a.expirationTimes, f2 = a.pendingLanes; 0 < f2; ) {
    var g2 = 31 - oc(f2), h = 1 << g2, k2 = e[g2];
    if (-1 === k2) {
      if (0 === (h & c) || 0 !== (h & d2)) e[g2] = vc(h, b2);
    } else k2 <= b2 && (a.expiredLanes |= h);
    f2 &= ~h;
  }
}
function xc(a) {
  a = a.pendingLanes & -1073741825;
  return 0 !== a ? a : a & 1073741824 ? 1073741824 : 0;
}
function yc() {
  var a = rc;
  rc <<= 1;
  0 === (rc & 4194240) && (rc = 64);
  return a;
}
function zc(a) {
  for (var b2 = [], c = 0; 31 > c; c++) b2.push(a);
  return b2;
}
function Ac(a, b2, c) {
  a.pendingLanes |= b2;
  536870912 !== b2 && (a.suspendedLanes = 0, a.pingedLanes = 0);
  a = a.eventTimes;
  b2 = 31 - oc(b2);
  a[b2] = c;
}
function Bc(a, b2) {
  var c = a.pendingLanes & ~b2;
  a.pendingLanes = b2;
  a.suspendedLanes = 0;
  a.pingedLanes = 0;
  a.expiredLanes &= b2;
  a.mutableReadLanes &= b2;
  a.entangledLanes &= b2;
  b2 = a.entanglements;
  var d2 = a.eventTimes;
  for (a = a.expirationTimes; 0 < c; ) {
    var e = 31 - oc(c), f2 = 1 << e;
    b2[e] = 0;
    d2[e] = -1;
    a[e] = -1;
    c &= ~f2;
  }
}
function Cc(a, b2) {
  var c = a.entangledLanes |= b2;
  for (a = a.entanglements; c; ) {
    var d2 = 31 - oc(c), e = 1 << d2;
    e & b2 | a[d2] & b2 && (a[d2] |= b2);
    c &= ~e;
  }
}
var C = 0;
function Dc(a) {
  a &= -a;
  return 1 < a ? 4 < a ? 0 !== (a & 268435455) ? 16 : 536870912 : 4 : 1;
}
var Ec, Fc, Gc, Hc, Ic, Jc = false, Kc = [], Lc = null, Mc = null, Nc = null, Oc = /* @__PURE__ */ new Map(), Pc = /* @__PURE__ */ new Map(), Qc = [], Rc = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
function Sc(a, b2) {
  switch (a) {
    case "focusin":
    case "focusout":
      Lc = null;
      break;
    case "dragenter":
    case "dragleave":
      Mc = null;
      break;
    case "mouseover":
    case "mouseout":
      Nc = null;
      break;
    case "pointerover":
    case "pointerout":
      Oc.delete(b2.pointerId);
      break;
    case "gotpointercapture":
    case "lostpointercapture":
      Pc.delete(b2.pointerId);
  }
}
function Tc(a, b2, c, d2, e, f2) {
  if (null === a || a.nativeEvent !== f2) return a = { blockedOn: b2, domEventName: c, eventSystemFlags: d2, nativeEvent: f2, targetContainers: [e] }, null !== b2 && (b2 = Cb(b2), null !== b2 && Fc(b2)), a;
  a.eventSystemFlags |= d2;
  b2 = a.targetContainers;
  null !== e && -1 === b2.indexOf(e) && b2.push(e);
  return a;
}
function Uc(a, b2, c, d2, e) {
  switch (b2) {
    case "focusin":
      return Lc = Tc(Lc, a, b2, c, d2, e), true;
    case "dragenter":
      return Mc = Tc(Mc, a, b2, c, d2, e), true;
    case "mouseover":
      return Nc = Tc(Nc, a, b2, c, d2, e), true;
    case "pointerover":
      var f2 = e.pointerId;
      Oc.set(f2, Tc(Oc.get(f2) || null, a, b2, c, d2, e));
      return true;
    case "gotpointercapture":
      return f2 = e.pointerId, Pc.set(f2, Tc(Pc.get(f2) || null, a, b2, c, d2, e)), true;
  }
  return false;
}
function Vc(a) {
  var b2 = Wc(a.target);
  if (null !== b2) {
    var c = Vb(b2);
    if (null !== c) {
      if (b2 = c.tag, 13 === b2) {
        if (b2 = Wb(c), null !== b2) {
          a.blockedOn = b2;
          Ic(a.priority, function() {
            Gc(c);
          });
          return;
        }
      } else if (3 === b2 && c.stateNode.current.memoizedState.isDehydrated) {
        a.blockedOn = 3 === c.tag ? c.stateNode.containerInfo : null;
        return;
      }
    }
  }
  a.blockedOn = null;
}
function Xc(a) {
  if (null !== a.blockedOn) return false;
  for (var b2 = a.targetContainers; 0 < b2.length; ) {
    var c = Yc(a.domEventName, a.eventSystemFlags, b2[0], a.nativeEvent);
    if (null === c) {
      c = a.nativeEvent;
      var d2 = new c.constructor(c.type, c);
      wb = d2;
      c.target.dispatchEvent(d2);
      wb = null;
    } else return b2 = Cb(c), null !== b2 && Fc(b2), a.blockedOn = c, false;
    b2.shift();
  }
  return true;
}
function Zc(a, b2, c) {
  Xc(a) && c.delete(b2);
}
function $c() {
  Jc = false;
  null !== Lc && Xc(Lc) && (Lc = null);
  null !== Mc && Xc(Mc) && (Mc = null);
  null !== Nc && Xc(Nc) && (Nc = null);
  Oc.forEach(Zc);
  Pc.forEach(Zc);
}
function ad(a, b2) {
  a.blockedOn === b2 && (a.blockedOn = null, Jc || (Jc = true, ca.unstable_scheduleCallback(ca.unstable_NormalPriority, $c)));
}
function bd(a) {
  function b2(b3) {
    return ad(b3, a);
  }
  if (0 < Kc.length) {
    ad(Kc[0], a);
    for (var c = 1; c < Kc.length; c++) {
      var d2 = Kc[c];
      d2.blockedOn === a && (d2.blockedOn = null);
    }
  }
  null !== Lc && ad(Lc, a);
  null !== Mc && ad(Mc, a);
  null !== Nc && ad(Nc, a);
  Oc.forEach(b2);
  Pc.forEach(b2);
  for (c = 0; c < Qc.length; c++) d2 = Qc[c], d2.blockedOn === a && (d2.blockedOn = null);
  for (; 0 < Qc.length && (c = Qc[0], null === c.blockedOn); ) Vc(c), null === c.blockedOn && Qc.shift();
}
var cd = ua.ReactCurrentBatchConfig, dd = true;
function ed(a, b2, c, d2) {
  var e = C, f2 = cd.transition;
  cd.transition = null;
  try {
    C = 1, fd(a, b2, c, d2);
  } finally {
    C = e, cd.transition = f2;
  }
}
function gd(a, b2, c, d2) {
  var e = C, f2 = cd.transition;
  cd.transition = null;
  try {
    C = 4, fd(a, b2, c, d2);
  } finally {
    C = e, cd.transition = f2;
  }
}
function fd(a, b2, c, d2) {
  if (dd) {
    var e = Yc(a, b2, c, d2);
    if (null === e) hd(a, b2, d2, id, c), Sc(a, d2);
    else if (Uc(e, a, b2, c, d2)) d2.stopPropagation();
    else if (Sc(a, d2), b2 & 4 && -1 < Rc.indexOf(a)) {
      for (; null !== e; ) {
        var f2 = Cb(e);
        null !== f2 && Ec(f2);
        f2 = Yc(a, b2, c, d2);
        null === f2 && hd(a, b2, d2, id, c);
        if (f2 === e) break;
        e = f2;
      }
      null !== e && d2.stopPropagation();
    } else hd(a, b2, d2, null, c);
  }
}
var id = null;
function Yc(a, b2, c, d2) {
  id = null;
  a = xb(d2);
  a = Wc(a);
  if (null !== a) if (b2 = Vb(a), null === b2) a = null;
  else if (c = b2.tag, 13 === c) {
    a = Wb(b2);
    if (null !== a) return a;
    a = null;
  } else if (3 === c) {
    if (b2.stateNode.current.memoizedState.isDehydrated) return 3 === b2.tag ? b2.stateNode.containerInfo : null;
    a = null;
  } else b2 !== a && (a = null);
  id = a;
  return null;
}
function jd(a) {
  switch (a) {
    case "cancel":
    case "click":
    case "close":
    case "contextmenu":
    case "copy":
    case "cut":
    case "auxclick":
    case "dblclick":
    case "dragend":
    case "dragstart":
    case "drop":
    case "focusin":
    case "focusout":
    case "input":
    case "invalid":
    case "keydown":
    case "keypress":
    case "keyup":
    case "mousedown":
    case "mouseup":
    case "paste":
    case "pause":
    case "play":
    case "pointercancel":
    case "pointerdown":
    case "pointerup":
    case "ratechange":
    case "reset":
    case "resize":
    case "seeked":
    case "submit":
    case "touchcancel":
    case "touchend":
    case "touchstart":
    case "volumechange":
    case "change":
    case "selectionchange":
    case "textInput":
    case "compositionstart":
    case "compositionend":
    case "compositionupdate":
    case "beforeblur":
    case "afterblur":
    case "beforeinput":
    case "blur":
    case "fullscreenchange":
    case "focus":
    case "hashchange":
    case "popstate":
    case "select":
    case "selectstart":
      return 1;
    case "drag":
    case "dragenter":
    case "dragexit":
    case "dragleave":
    case "dragover":
    case "mousemove":
    case "mouseout":
    case "mouseover":
    case "pointermove":
    case "pointerout":
    case "pointerover":
    case "scroll":
    case "toggle":
    case "touchmove":
    case "wheel":
    case "mouseenter":
    case "mouseleave":
    case "pointerenter":
    case "pointerleave":
      return 4;
    case "message":
      switch (ec()) {
        case fc:
          return 1;
        case gc:
          return 4;
        case hc:
        case ic:
          return 16;
        case jc:
          return 536870912;
        default:
          return 16;
      }
    default:
      return 16;
  }
}
var kd = null, ld = null, md = null;
function nd() {
  if (md) return md;
  var a, b2 = ld, c = b2.length, d2, e = "value" in kd ? kd.value : kd.textContent, f2 = e.length;
  for (a = 0; a < c && b2[a] === e[a]; a++) ;
  var g2 = c - a;
  for (d2 = 1; d2 <= g2 && b2[c - d2] === e[f2 - d2]; d2++) ;
  return md = e.slice(a, 1 < d2 ? 1 - d2 : void 0);
}
function od(a) {
  var b2 = a.keyCode;
  "charCode" in a ? (a = a.charCode, 0 === a && 13 === b2 && (a = 13)) : a = b2;
  10 === a && (a = 13);
  return 32 <= a || 13 === a ? a : 0;
}
function pd() {
  return true;
}
function qd() {
  return false;
}
function rd(a) {
  function b2(b3, d2, e, f2, g2) {
    this._reactName = b3;
    this._targetInst = e;
    this.type = d2;
    this.nativeEvent = f2;
    this.target = g2;
    this.currentTarget = null;
    for (var c in a) a.hasOwnProperty(c) && (b3 = a[c], this[c] = b3 ? b3(f2) : f2[c]);
    this.isDefaultPrevented = (null != f2.defaultPrevented ? f2.defaultPrevented : false === f2.returnValue) ? pd : qd;
    this.isPropagationStopped = qd;
    return this;
  }
  A$1(b2.prototype, { preventDefault: function() {
    this.defaultPrevented = true;
    var a2 = this.nativeEvent;
    a2 && (a2.preventDefault ? a2.preventDefault() : "unknown" !== typeof a2.returnValue && (a2.returnValue = false), this.isDefaultPrevented = pd);
  }, stopPropagation: function() {
    var a2 = this.nativeEvent;
    a2 && (a2.stopPropagation ? a2.stopPropagation() : "unknown" !== typeof a2.cancelBubble && (a2.cancelBubble = true), this.isPropagationStopped = pd);
  }, persist: function() {
  }, isPersistent: pd });
  return b2;
}
var sd = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(a) {
  return a.timeStamp || Date.now();
}, defaultPrevented: 0, isTrusted: 0 }, td = rd(sd), ud = A$1({}, sd, { view: 0, detail: 0 }), vd = rd(ud), wd, xd, yd, Ad = A$1({}, ud, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: zd, button: 0, buttons: 0, relatedTarget: function(a) {
  return void 0 === a.relatedTarget ? a.fromElement === a.srcElement ? a.toElement : a.fromElement : a.relatedTarget;
}, movementX: function(a) {
  if ("movementX" in a) return a.movementX;
  a !== yd && (yd && "mousemove" === a.type ? (wd = a.screenX - yd.screenX, xd = a.screenY - yd.screenY) : xd = wd = 0, yd = a);
  return wd;
}, movementY: function(a) {
  return "movementY" in a ? a.movementY : xd;
} }), Bd = rd(Ad), Cd = A$1({}, Ad, { dataTransfer: 0 }), Dd = rd(Cd), Ed = A$1({}, ud, { relatedTarget: 0 }), Fd = rd(Ed), Gd = A$1({}, sd, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), Hd = rd(Gd), Id = A$1({}, sd, { clipboardData: function(a) {
  return "clipboardData" in a ? a.clipboardData : window.clipboardData;
} }), Jd = rd(Id), Kd = A$1({}, sd, { data: 0 }), Ld = rd(Kd), Md = {
  Esc: "Escape",
  Spacebar: " ",
  Left: "ArrowLeft",
  Up: "ArrowUp",
  Right: "ArrowRight",
  Down: "ArrowDown",
  Del: "Delete",
  Win: "OS",
  Menu: "ContextMenu",
  Apps: "ContextMenu",
  Scroll: "ScrollLock",
  MozPrintableKey: "Unidentified"
}, Nd = {
  8: "Backspace",
  9: "Tab",
  12: "Clear",
  13: "Enter",
  16: "Shift",
  17: "Control",
  18: "Alt",
  19: "Pause",
  20: "CapsLock",
  27: "Escape",
  32: " ",
  33: "PageUp",
  34: "PageDown",
  35: "End",
  36: "Home",
  37: "ArrowLeft",
  38: "ArrowUp",
  39: "ArrowRight",
  40: "ArrowDown",
  45: "Insert",
  46: "Delete",
  112: "F1",
  113: "F2",
  114: "F3",
  115: "F4",
  116: "F5",
  117: "F6",
  118: "F7",
  119: "F8",
  120: "F9",
  121: "F10",
  122: "F11",
  123: "F12",
  144: "NumLock",
  145: "ScrollLock",
  224: "Meta"
}, Od = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
function Pd(a) {
  var b2 = this.nativeEvent;
  return b2.getModifierState ? b2.getModifierState(a) : (a = Od[a]) ? !!b2[a] : false;
}
function zd() {
  return Pd;
}
var Qd = A$1({}, ud, { key: function(a) {
  if (a.key) {
    var b2 = Md[a.key] || a.key;
    if ("Unidentified" !== b2) return b2;
  }
  return "keypress" === a.type ? (a = od(a), 13 === a ? "Enter" : String.fromCharCode(a)) : "keydown" === a.type || "keyup" === a.type ? Nd[a.keyCode] || "Unidentified" : "";
}, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: zd, charCode: function(a) {
  return "keypress" === a.type ? od(a) : 0;
}, keyCode: function(a) {
  return "keydown" === a.type || "keyup" === a.type ? a.keyCode : 0;
}, which: function(a) {
  return "keypress" === a.type ? od(a) : "keydown" === a.type || "keyup" === a.type ? a.keyCode : 0;
} }), Rd = rd(Qd), Sd = A$1({}, Ad, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Td = rd(Sd), Ud = A$1({}, ud, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: zd }), Vd = rd(Ud), Wd = A$1({}, sd, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), Xd = rd(Wd), Yd = A$1({}, Ad, {
  deltaX: function(a) {
    return "deltaX" in a ? a.deltaX : "wheelDeltaX" in a ? -a.wheelDeltaX : 0;
  },
  deltaY: function(a) {
    return "deltaY" in a ? a.deltaY : "wheelDeltaY" in a ? -a.wheelDeltaY : "wheelDelta" in a ? -a.wheelDelta : 0;
  },
  deltaZ: 0,
  deltaMode: 0
}), Zd = rd(Yd), $d = [9, 13, 27, 32], ae$1 = ia && "CompositionEvent" in window, be = null;
ia && "documentMode" in document && (be = document.documentMode);
var ce$1 = ia && "TextEvent" in window && !be, de$1 = ia && (!ae$1 || be && 8 < be && 11 >= be), ee$1 = String.fromCharCode(32), fe$1 = false;
function ge$1(a, b2) {
  switch (a) {
    case "keyup":
      return -1 !== $d.indexOf(b2.keyCode);
    case "keydown":
      return 229 !== b2.keyCode;
    case "keypress":
    case "mousedown":
    case "focusout":
      return true;
    default:
      return false;
  }
}
function he$1(a) {
  a = a.detail;
  return "object" === typeof a && "data" in a ? a.data : null;
}
var ie$1 = false;
function je$1(a, b2) {
  switch (a) {
    case "compositionend":
      return he$1(b2);
    case "keypress":
      if (32 !== b2.which) return null;
      fe$1 = true;
      return ee$1;
    case "textInput":
      return a = b2.data, a === ee$1 && fe$1 ? null : a;
    default:
      return null;
  }
}
function ke$1(a, b2) {
  if (ie$1) return "compositionend" === a || !ae$1 && ge$1(a, b2) ? (a = nd(), md = ld = kd = null, ie$1 = false, a) : null;
  switch (a) {
    case "paste":
      return null;
    case "keypress":
      if (!(b2.ctrlKey || b2.altKey || b2.metaKey) || b2.ctrlKey && b2.altKey) {
        if (b2.char && 1 < b2.char.length) return b2.char;
        if (b2.which) return String.fromCharCode(b2.which);
      }
      return null;
    case "compositionend":
      return de$1 && "ko" !== b2.locale ? null : b2.data;
    default:
      return null;
  }
}
var le$1 = { color: true, date: true, datetime: true, "datetime-local": true, email: true, month: true, number: true, password: true, range: true, search: true, tel: true, text: true, time: true, url: true, week: true };
function me$1(a) {
  var b2 = a && a.nodeName && a.nodeName.toLowerCase();
  return "input" === b2 ? !!le$1[a.type] : "textarea" === b2 ? true : false;
}
function ne(a, b2, c, d2) {
  Eb(d2);
  b2 = oe$1(b2, "onChange");
  0 < b2.length && (c = new td("onChange", "change", null, c, d2), a.push({ event: c, listeners: b2 }));
}
var pe$1 = null, qe$1 = null;
function re(a) {
  se$1(a, 0);
}
function te(a) {
  var b2 = ue$1(a);
  if (Wa(b2)) return a;
}
function ve$1(a, b2) {
  if ("change" === a) return b2;
}
var we$1 = false;
if (ia) {
  var xe$1;
  if (ia) {
    var ye$1 = "oninput" in document;
    if (!ye$1) {
      var ze$1 = document.createElement("div");
      ze$1.setAttribute("oninput", "return;");
      ye$1 = "function" === typeof ze$1.oninput;
    }
    xe$1 = ye$1;
  } else xe$1 = false;
  we$1 = xe$1 && (!document.documentMode || 9 < document.documentMode);
}
function Ae$1() {
  pe$1 && (pe$1.detachEvent("onpropertychange", Be$1), qe$1 = pe$1 = null);
}
function Be$1(a) {
  if ("value" === a.propertyName && te(qe$1)) {
    var b2 = [];
    ne(b2, qe$1, a, xb(a));
    Jb(re, b2);
  }
}
function Ce$1(a, b2, c) {
  "focusin" === a ? (Ae$1(), pe$1 = b2, qe$1 = c, pe$1.attachEvent("onpropertychange", Be$1)) : "focusout" === a && Ae$1();
}
function De$1(a) {
  if ("selectionchange" === a || "keyup" === a || "keydown" === a) return te(qe$1);
}
function Ee$1(a, b2) {
  if ("click" === a) return te(b2);
}
function Fe$1(a, b2) {
  if ("input" === a || "change" === a) return te(b2);
}
function Ge$1(a, b2) {
  return a === b2 && (0 !== a || 1 / a === 1 / b2) || a !== a && b2 !== b2;
}
var He$1 = "function" === typeof Object.is ? Object.is : Ge$1;
function Ie$1(a, b2) {
  if (He$1(a, b2)) return true;
  if ("object" !== typeof a || null === a || "object" !== typeof b2 || null === b2) return false;
  var c = Object.keys(a), d2 = Object.keys(b2);
  if (c.length !== d2.length) return false;
  for (d2 = 0; d2 < c.length; d2++) {
    var e = c[d2];
    if (!ja.call(b2, e) || !He$1(a[e], b2[e])) return false;
  }
  return true;
}
function Je$1(a) {
  for (; a && a.firstChild; ) a = a.firstChild;
  return a;
}
function Ke$1(a, b2) {
  var c = Je$1(a);
  a = 0;
  for (var d2; c; ) {
    if (3 === c.nodeType) {
      d2 = a + c.textContent.length;
      if (a <= b2 && d2 >= b2) return { node: c, offset: b2 - a };
      a = d2;
    }
    a: {
      for (; c; ) {
        if (c.nextSibling) {
          c = c.nextSibling;
          break a;
        }
        c = c.parentNode;
      }
      c = void 0;
    }
    c = Je$1(c);
  }
}
function Le$1(a, b2) {
  return a && b2 ? a === b2 ? true : a && 3 === a.nodeType ? false : b2 && 3 === b2.nodeType ? Le$1(a, b2.parentNode) : "contains" in a ? a.contains(b2) : a.compareDocumentPosition ? !!(a.compareDocumentPosition(b2) & 16) : false : false;
}
function Me$1() {
  for (var a = window, b2 = Xa(); b2 instanceof a.HTMLIFrameElement; ) {
    try {
      var c = "string" === typeof b2.contentWindow.location.href;
    } catch (d2) {
      c = false;
    }
    if (c) a = b2.contentWindow;
    else break;
    b2 = Xa(a.document);
  }
  return b2;
}
function Ne$1(a) {
  var b2 = a && a.nodeName && a.nodeName.toLowerCase();
  return b2 && ("input" === b2 && ("text" === a.type || "search" === a.type || "tel" === a.type || "url" === a.type || "password" === a.type) || "textarea" === b2 || "true" === a.contentEditable);
}
function Oe$1(a) {
  var b2 = Me$1(), c = a.focusedElem, d2 = a.selectionRange;
  if (b2 !== c && c && c.ownerDocument && Le$1(c.ownerDocument.documentElement, c)) {
    if (null !== d2 && Ne$1(c)) {
      if (b2 = d2.start, a = d2.end, void 0 === a && (a = b2), "selectionStart" in c) c.selectionStart = b2, c.selectionEnd = Math.min(a, c.value.length);
      else if (a = (b2 = c.ownerDocument || document) && b2.defaultView || window, a.getSelection) {
        a = a.getSelection();
        var e = c.textContent.length, f2 = Math.min(d2.start, e);
        d2 = void 0 === d2.end ? f2 : Math.min(d2.end, e);
        !a.extend && f2 > d2 && (e = d2, d2 = f2, f2 = e);
        e = Ke$1(c, f2);
        var g2 = Ke$1(
          c,
          d2
        );
        e && g2 && (1 !== a.rangeCount || a.anchorNode !== e.node || a.anchorOffset !== e.offset || a.focusNode !== g2.node || a.focusOffset !== g2.offset) && (b2 = b2.createRange(), b2.setStart(e.node, e.offset), a.removeAllRanges(), f2 > d2 ? (a.addRange(b2), a.extend(g2.node, g2.offset)) : (b2.setEnd(g2.node, g2.offset), a.addRange(b2)));
      }
    }
    b2 = [];
    for (a = c; a = a.parentNode; ) 1 === a.nodeType && b2.push({ element: a, left: a.scrollLeft, top: a.scrollTop });
    "function" === typeof c.focus && c.focus();
    for (c = 0; c < b2.length; c++) a = b2[c], a.element.scrollLeft = a.left, a.element.scrollTop = a.top;
  }
}
var Pe$1 = ia && "documentMode" in document && 11 >= document.documentMode, Qe$1 = null, Re = null, Se$1 = null, Te$1 = false;
function Ue$1(a, b2, c) {
  var d2 = c.window === c ? c.document : 9 === c.nodeType ? c : c.ownerDocument;
  Te$1 || null == Qe$1 || Qe$1 !== Xa(d2) || (d2 = Qe$1, "selectionStart" in d2 && Ne$1(d2) ? d2 = { start: d2.selectionStart, end: d2.selectionEnd } : (d2 = (d2.ownerDocument && d2.ownerDocument.defaultView || window).getSelection(), d2 = { anchorNode: d2.anchorNode, anchorOffset: d2.anchorOffset, focusNode: d2.focusNode, focusOffset: d2.focusOffset }), Se$1 && Ie$1(Se$1, d2) || (Se$1 = d2, d2 = oe$1(Re, "onSelect"), 0 < d2.length && (b2 = new td("onSelect", "select", null, b2, c), a.push({ event: b2, listeners: d2 }), b2.target = Qe$1)));
}
function Ve$1(a, b2) {
  var c = {};
  c[a.toLowerCase()] = b2.toLowerCase();
  c["Webkit" + a] = "webkit" + b2;
  c["Moz" + a] = "moz" + b2;
  return c;
}
var We$1 = { animationend: Ve$1("Animation", "AnimationEnd"), animationiteration: Ve$1("Animation", "AnimationIteration"), animationstart: Ve$1("Animation", "AnimationStart"), transitionend: Ve$1("Transition", "TransitionEnd") }, Xe$1 = {}, Ye$1 = {};
ia && (Ye$1 = document.createElement("div").style, "AnimationEvent" in window || (delete We$1.animationend.animation, delete We$1.animationiteration.animation, delete We$1.animationstart.animation), "TransitionEvent" in window || delete We$1.transitionend.transition);
function Ze$1(a) {
  if (Xe$1[a]) return Xe$1[a];
  if (!We$1[a]) return a;
  var b2 = We$1[a], c;
  for (c in b2) if (b2.hasOwnProperty(c) && c in Ye$1) return Xe$1[a] = b2[c];
  return a;
}
var $e$1 = Ze$1("animationend"), af = Ze$1("animationiteration"), bf = Ze$1("animationstart"), cf = Ze$1("transitionend"), df = /* @__PURE__ */ new Map(), ef = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
function ff(a, b2) {
  df.set(a, b2);
  fa(b2, [a]);
}
for (var gf = 0; gf < ef.length; gf++) {
  var hf = ef[gf], jf = hf.toLowerCase(), kf = hf[0].toUpperCase() + hf.slice(1);
  ff(jf, "on" + kf);
}
ff($e$1, "onAnimationEnd");
ff(af, "onAnimationIteration");
ff(bf, "onAnimationStart");
ff("dblclick", "onDoubleClick");
ff("focusin", "onFocus");
ff("focusout", "onBlur");
ff(cf, "onTransitionEnd");
ha("onMouseEnter", ["mouseout", "mouseover"]);
ha("onMouseLeave", ["mouseout", "mouseover"]);
ha("onPointerEnter", ["pointerout", "pointerover"]);
ha("onPointerLeave", ["pointerout", "pointerover"]);
fa("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" "));
fa("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" "));
fa("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]);
fa("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" "));
fa("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" "));
fa("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
var lf = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), mf = new Set("cancel close invalid load scroll toggle".split(" ").concat(lf));
function nf(a, b2, c) {
  var d2 = a.type || "unknown-event";
  a.currentTarget = c;
  Ub(d2, b2, void 0, a);
  a.currentTarget = null;
}
function se$1(a, b2) {
  b2 = 0 !== (b2 & 4);
  for (var c = 0; c < a.length; c++) {
    var d2 = a[c], e = d2.event;
    d2 = d2.listeners;
    a: {
      var f2 = void 0;
      if (b2) for (var g2 = d2.length - 1; 0 <= g2; g2--) {
        var h = d2[g2], k2 = h.instance, l4 = h.currentTarget;
        h = h.listener;
        if (k2 !== f2 && e.isPropagationStopped()) break a;
        nf(e, h, l4);
        f2 = k2;
      }
      else for (g2 = 0; g2 < d2.length; g2++) {
        h = d2[g2];
        k2 = h.instance;
        l4 = h.currentTarget;
        h = h.listener;
        if (k2 !== f2 && e.isPropagationStopped()) break a;
        nf(e, h, l4);
        f2 = k2;
      }
    }
  }
  if (Qb) throw a = Rb, Qb = false, Rb = null, a;
}
function D$1(a, b2) {
  var c = b2[of];
  void 0 === c && (c = b2[of] = /* @__PURE__ */ new Set());
  var d2 = a + "__bubble";
  c.has(d2) || (pf(b2, a, 2, false), c.add(d2));
}
function qf(a, b2, c) {
  var d2 = 0;
  b2 && (d2 |= 4);
  pf(c, a, d2, b2);
}
var rf = "_reactListening" + Math.random().toString(36).slice(2);
function sf(a) {
  if (!a[rf]) {
    a[rf] = true;
    da.forEach(function(b3) {
      "selectionchange" !== b3 && (mf.has(b3) || qf(b3, false, a), qf(b3, true, a));
    });
    var b2 = 9 === a.nodeType ? a : a.ownerDocument;
    null === b2 || b2[rf] || (b2[rf] = true, qf("selectionchange", false, b2));
  }
}
function pf(a, b2, c, d2) {
  switch (jd(b2)) {
    case 1:
      var e = ed;
      break;
    case 4:
      e = gd;
      break;
    default:
      e = fd;
  }
  c = e.bind(null, b2, c, a);
  e = void 0;
  !Lb || "touchstart" !== b2 && "touchmove" !== b2 && "wheel" !== b2 || (e = true);
  d2 ? void 0 !== e ? a.addEventListener(b2, c, { capture: true, passive: e }) : a.addEventListener(b2, c, true) : void 0 !== e ? a.addEventListener(b2, c, { passive: e }) : a.addEventListener(b2, c, false);
}
function hd(a, b2, c, d2, e) {
  var f2 = d2;
  if (0 === (b2 & 1) && 0 === (b2 & 2) && null !== d2) a: for (; ; ) {
    if (null === d2) return;
    var g2 = d2.tag;
    if (3 === g2 || 4 === g2) {
      var h = d2.stateNode.containerInfo;
      if (h === e || 8 === h.nodeType && h.parentNode === e) break;
      if (4 === g2) for (g2 = d2.return; null !== g2; ) {
        var k2 = g2.tag;
        if (3 === k2 || 4 === k2) {
          if (k2 = g2.stateNode.containerInfo, k2 === e || 8 === k2.nodeType && k2.parentNode === e) return;
        }
        g2 = g2.return;
      }
      for (; null !== h; ) {
        g2 = Wc(h);
        if (null === g2) return;
        k2 = g2.tag;
        if (5 === k2 || 6 === k2) {
          d2 = f2 = g2;
          continue a;
        }
        h = h.parentNode;
      }
    }
    d2 = d2.return;
  }
  Jb(function() {
    var d3 = f2, e2 = xb(c), g3 = [];
    a: {
      var h2 = df.get(a);
      if (void 0 !== h2) {
        var k3 = td, n2 = a;
        switch (a) {
          case "keypress":
            if (0 === od(c)) break a;
          case "keydown":
          case "keyup":
            k3 = Rd;
            break;
          case "focusin":
            n2 = "focus";
            k3 = Fd;
            break;
          case "focusout":
            n2 = "blur";
            k3 = Fd;
            break;
          case "beforeblur":
          case "afterblur":
            k3 = Fd;
            break;
          case "click":
            if (2 === c.button) break a;
          case "auxclick":
          case "dblclick":
          case "mousedown":
          case "mousemove":
          case "mouseup":
          case "mouseout":
          case "mouseover":
          case "contextmenu":
            k3 = Bd;
            break;
          case "drag":
          case "dragend":
          case "dragenter":
          case "dragexit":
          case "dragleave":
          case "dragover":
          case "dragstart":
          case "drop":
            k3 = Dd;
            break;
          case "touchcancel":
          case "touchend":
          case "touchmove":
          case "touchstart":
            k3 = Vd;
            break;
          case $e$1:
          case af:
          case bf:
            k3 = Hd;
            break;
          case cf:
            k3 = Xd;
            break;
          case "scroll":
            k3 = vd;
            break;
          case "wheel":
            k3 = Zd;
            break;
          case "copy":
          case "cut":
          case "paste":
            k3 = Jd;
            break;
          case "gotpointercapture":
          case "lostpointercapture":
          case "pointercancel":
          case "pointerdown":
          case "pointermove":
          case "pointerout":
          case "pointerover":
          case "pointerup":
            k3 = Td;
        }
        var t2 = 0 !== (b2 & 4), J2 = !t2 && "scroll" === a, x2 = t2 ? null !== h2 ? h2 + "Capture" : null : h2;
        t2 = [];
        for (var w2 = d3, u2; null !== w2; ) {
          u2 = w2;
          var F2 = u2.stateNode;
          5 === u2.tag && null !== F2 && (u2 = F2, null !== x2 && (F2 = Kb(w2, x2), null != F2 && t2.push(tf(w2, F2, u2))));
          if (J2) break;
          w2 = w2.return;
        }
        0 < t2.length && (h2 = new k3(h2, n2, null, c, e2), g3.push({ event: h2, listeners: t2 }));
      }
    }
    if (0 === (b2 & 7)) {
      a: {
        h2 = "mouseover" === a || "pointerover" === a;
        k3 = "mouseout" === a || "pointerout" === a;
        if (h2 && c !== wb && (n2 = c.relatedTarget || c.fromElement) && (Wc(n2) || n2[uf])) break a;
        if (k3 || h2) {
          h2 = e2.window === e2 ? e2 : (h2 = e2.ownerDocument) ? h2.defaultView || h2.parentWindow : window;
          if (k3) {
            if (n2 = c.relatedTarget || c.toElement, k3 = d3, n2 = n2 ? Wc(n2) : null, null !== n2 && (J2 = Vb(n2), n2 !== J2 || 5 !== n2.tag && 6 !== n2.tag)) n2 = null;
          } else k3 = null, n2 = d3;
          if (k3 !== n2) {
            t2 = Bd;
            F2 = "onMouseLeave";
            x2 = "onMouseEnter";
            w2 = "mouse";
            if ("pointerout" === a || "pointerover" === a) t2 = Td, F2 = "onPointerLeave", x2 = "onPointerEnter", w2 = "pointer";
            J2 = null == k3 ? h2 : ue$1(k3);
            u2 = null == n2 ? h2 : ue$1(n2);
            h2 = new t2(F2, w2 + "leave", k3, c, e2);
            h2.target = J2;
            h2.relatedTarget = u2;
            F2 = null;
            Wc(e2) === d3 && (t2 = new t2(x2, w2 + "enter", n2, c, e2), t2.target = u2, t2.relatedTarget = J2, F2 = t2);
            J2 = F2;
            if (k3 && n2) b: {
              t2 = k3;
              x2 = n2;
              w2 = 0;
              for (u2 = t2; u2; u2 = vf(u2)) w2++;
              u2 = 0;
              for (F2 = x2; F2; F2 = vf(F2)) u2++;
              for (; 0 < w2 - u2; ) t2 = vf(t2), w2--;
              for (; 0 < u2 - w2; ) x2 = vf(x2), u2--;
              for (; w2--; ) {
                if (t2 === x2 || null !== x2 && t2 === x2.alternate) break b;
                t2 = vf(t2);
                x2 = vf(x2);
              }
              t2 = null;
            }
            else t2 = null;
            null !== k3 && wf(g3, h2, k3, t2, false);
            null !== n2 && null !== J2 && wf(g3, J2, n2, t2, true);
          }
        }
      }
      a: {
        h2 = d3 ? ue$1(d3) : window;
        k3 = h2.nodeName && h2.nodeName.toLowerCase();
        if ("select" === k3 || "input" === k3 && "file" === h2.type) var na = ve$1;
        else if (me$1(h2)) if (we$1) na = Fe$1;
        else {
          na = De$1;
          var xa = Ce$1;
        }
        else (k3 = h2.nodeName) && "input" === k3.toLowerCase() && ("checkbox" === h2.type || "radio" === h2.type) && (na = Ee$1);
        if (na && (na = na(a, d3))) {
          ne(g3, na, c, e2);
          break a;
        }
        xa && xa(a, h2, d3);
        "focusout" === a && (xa = h2._wrapperState) && xa.controlled && "number" === h2.type && cb(h2, "number", h2.value);
      }
      xa = d3 ? ue$1(d3) : window;
      switch (a) {
        case "focusin":
          if (me$1(xa) || "true" === xa.contentEditable) Qe$1 = xa, Re = d3, Se$1 = null;
          break;
        case "focusout":
          Se$1 = Re = Qe$1 = null;
          break;
        case "mousedown":
          Te$1 = true;
          break;
        case "contextmenu":
        case "mouseup":
        case "dragend":
          Te$1 = false;
          Ue$1(g3, c, e2);
          break;
        case "selectionchange":
          if (Pe$1) break;
        case "keydown":
        case "keyup":
          Ue$1(g3, c, e2);
      }
      var $a;
      if (ae$1) b: {
        switch (a) {
          case "compositionstart":
            var ba = "onCompositionStart";
            break b;
          case "compositionend":
            ba = "onCompositionEnd";
            break b;
          case "compositionupdate":
            ba = "onCompositionUpdate";
            break b;
        }
        ba = void 0;
      }
      else ie$1 ? ge$1(a, c) && (ba = "onCompositionEnd") : "keydown" === a && 229 === c.keyCode && (ba = "onCompositionStart");
      ba && (de$1 && "ko" !== c.locale && (ie$1 || "onCompositionStart" !== ba ? "onCompositionEnd" === ba && ie$1 && ($a = nd()) : (kd = e2, ld = "value" in kd ? kd.value : kd.textContent, ie$1 = true)), xa = oe$1(d3, ba), 0 < xa.length && (ba = new Ld(ba, a, null, c, e2), g3.push({ event: ba, listeners: xa }), $a ? ba.data = $a : ($a = he$1(c), null !== $a && (ba.data = $a))));
      if ($a = ce$1 ? je$1(a, c) : ke$1(a, c)) d3 = oe$1(d3, "onBeforeInput"), 0 < d3.length && (e2 = new Ld("onBeforeInput", "beforeinput", null, c, e2), g3.push({ event: e2, listeners: d3 }), e2.data = $a);
    }
    se$1(g3, b2);
  });
}
function tf(a, b2, c) {
  return { instance: a, listener: b2, currentTarget: c };
}
function oe$1(a, b2) {
  for (var c = b2 + "Capture", d2 = []; null !== a; ) {
    var e = a, f2 = e.stateNode;
    5 === e.tag && null !== f2 && (e = f2, f2 = Kb(a, c), null != f2 && d2.unshift(tf(a, f2, e)), f2 = Kb(a, b2), null != f2 && d2.push(tf(a, f2, e)));
    a = a.return;
  }
  return d2;
}
function vf(a) {
  if (null === a) return null;
  do
    a = a.return;
  while (a && 5 !== a.tag);
  return a ? a : null;
}
function wf(a, b2, c, d2, e) {
  for (var f2 = b2._reactName, g2 = []; null !== c && c !== d2; ) {
    var h = c, k2 = h.alternate, l4 = h.stateNode;
    if (null !== k2 && k2 === d2) break;
    5 === h.tag && null !== l4 && (h = l4, e ? (k2 = Kb(c, f2), null != k2 && g2.unshift(tf(c, k2, h))) : e || (k2 = Kb(c, f2), null != k2 && g2.push(tf(c, k2, h))));
    c = c.return;
  }
  0 !== g2.length && a.push({ event: b2, listeners: g2 });
}
var xf = /\r\n?/g, yf = /\u0000|\uFFFD/g;
function zf(a) {
  return ("string" === typeof a ? a : "" + a).replace(xf, "\n").replace(yf, "");
}
function Af(a, b2, c) {
  b2 = zf(b2);
  if (zf(a) !== b2 && c) throw Error(p(425));
}
function Bf() {
}
var Cf = null, Df = null;
function Ef(a, b2) {
  return "textarea" === a || "noscript" === a || "string" === typeof b2.children || "number" === typeof b2.children || "object" === typeof b2.dangerouslySetInnerHTML && null !== b2.dangerouslySetInnerHTML && null != b2.dangerouslySetInnerHTML.__html;
}
var Ff = "function" === typeof setTimeout ? setTimeout : void 0, Gf = "function" === typeof clearTimeout ? clearTimeout : void 0, Hf = "function" === typeof Promise ? Promise : void 0, Jf = "function" === typeof queueMicrotask ? queueMicrotask : "undefined" !== typeof Hf ? function(a) {
  return Hf.resolve(null).then(a).catch(If);
} : Ff;
function If(a) {
  setTimeout(function() {
    throw a;
  });
}
function Kf(a, b2) {
  var c = b2, d2 = 0;
  do {
    var e = c.nextSibling;
    a.removeChild(c);
    if (e && 8 === e.nodeType) if (c = e.data, "/$" === c) {
      if (0 === d2) {
        a.removeChild(e);
        bd(b2);
        return;
      }
      d2--;
    } else "$" !== c && "$?" !== c && "$!" !== c || d2++;
    c = e;
  } while (c);
  bd(b2);
}
function Lf(a) {
  for (; null != a; a = a.nextSibling) {
    var b2 = a.nodeType;
    if (1 === b2 || 3 === b2) break;
    if (8 === b2) {
      b2 = a.data;
      if ("$" === b2 || "$!" === b2 || "$?" === b2) break;
      if ("/$" === b2) return null;
    }
  }
  return a;
}
function Mf(a) {
  a = a.previousSibling;
  for (var b2 = 0; a; ) {
    if (8 === a.nodeType) {
      var c = a.data;
      if ("$" === c || "$!" === c || "$?" === c) {
        if (0 === b2) return a;
        b2--;
      } else "/$" === c && b2++;
    }
    a = a.previousSibling;
  }
  return null;
}
var Nf = Math.random().toString(36).slice(2), Of = "__reactFiber$" + Nf, Pf = "__reactProps$" + Nf, uf = "__reactContainer$" + Nf, of = "__reactEvents$" + Nf, Qf = "__reactListeners$" + Nf, Rf = "__reactHandles$" + Nf;
function Wc(a) {
  var b2 = a[Of];
  if (b2) return b2;
  for (var c = a.parentNode; c; ) {
    if (b2 = c[uf] || c[Of]) {
      c = b2.alternate;
      if (null !== b2.child || null !== c && null !== c.child) for (a = Mf(a); null !== a; ) {
        if (c = a[Of]) return c;
        a = Mf(a);
      }
      return b2;
    }
    a = c;
    c = a.parentNode;
  }
  return null;
}
function Cb(a) {
  a = a[Of] || a[uf];
  return !a || 5 !== a.tag && 6 !== a.tag && 13 !== a.tag && 3 !== a.tag ? null : a;
}
function ue$1(a) {
  if (5 === a.tag || 6 === a.tag) return a.stateNode;
  throw Error(p(33));
}
function Db(a) {
  return a[Pf] || null;
}
var Sf = [], Tf = -1;
function Uf(a) {
  return { current: a };
}
function E$1(a) {
  0 > Tf || (a.current = Sf[Tf], Sf[Tf] = null, Tf--);
}
function G(a, b2) {
  Tf++;
  Sf[Tf] = a.current;
  a.current = b2;
}
var Vf = {}, H$1 = Uf(Vf), Wf = Uf(false), Xf = Vf;
function Yf(a, b2) {
  var c = a.type.contextTypes;
  if (!c) return Vf;
  var d2 = a.stateNode;
  if (d2 && d2.__reactInternalMemoizedUnmaskedChildContext === b2) return d2.__reactInternalMemoizedMaskedChildContext;
  var e = {}, f2;
  for (f2 in c) e[f2] = b2[f2];
  d2 && (a = a.stateNode, a.__reactInternalMemoizedUnmaskedChildContext = b2, a.__reactInternalMemoizedMaskedChildContext = e);
  return e;
}
function Zf(a) {
  a = a.childContextTypes;
  return null !== a && void 0 !== a;
}
function $f() {
  E$1(Wf);
  E$1(H$1);
}
function ag(a, b2, c) {
  if (H$1.current !== Vf) throw Error(p(168));
  G(H$1, b2);
  G(Wf, c);
}
function bg(a, b2, c) {
  var d2 = a.stateNode;
  b2 = b2.childContextTypes;
  if ("function" !== typeof d2.getChildContext) return c;
  d2 = d2.getChildContext();
  for (var e in d2) if (!(e in b2)) throw Error(p(108, Ra(a) || "Unknown", e));
  return A$1({}, c, d2);
}
function cg(a) {
  a = (a = a.stateNode) && a.__reactInternalMemoizedMergedChildContext || Vf;
  Xf = H$1.current;
  G(H$1, a);
  G(Wf, Wf.current);
  return true;
}
function dg(a, b2, c) {
  var d2 = a.stateNode;
  if (!d2) throw Error(p(169));
  c ? (a = bg(a, b2, Xf), d2.__reactInternalMemoizedMergedChildContext = a, E$1(Wf), E$1(H$1), G(H$1, a)) : E$1(Wf);
  G(Wf, c);
}
var eg = null, fg = false, gg = false;
function hg(a) {
  null === eg ? eg = [a] : eg.push(a);
}
function ig(a) {
  fg = true;
  hg(a);
}
function jg() {
  if (!gg && null !== eg) {
    gg = true;
    var a = 0, b2 = C;
    try {
      var c = eg;
      for (C = 1; a < c.length; a++) {
        var d2 = c[a];
        do
          d2 = d2(true);
        while (null !== d2);
      }
      eg = null;
      fg = false;
    } catch (e) {
      throw null !== eg && (eg = eg.slice(a + 1)), ac(fc, jg), e;
    } finally {
      C = b2, gg = false;
    }
  }
  return null;
}
var kg = [], lg = 0, mg = null, ng = 0, og = [], pg = 0, qg = null, rg = 1, sg = "";
function tg(a, b2) {
  kg[lg++] = ng;
  kg[lg++] = mg;
  mg = a;
  ng = b2;
}
function ug(a, b2, c) {
  og[pg++] = rg;
  og[pg++] = sg;
  og[pg++] = qg;
  qg = a;
  var d2 = rg;
  a = sg;
  var e = 32 - oc(d2) - 1;
  d2 &= ~(1 << e);
  c += 1;
  var f2 = 32 - oc(b2) + e;
  if (30 < f2) {
    var g2 = e - e % 5;
    f2 = (d2 & (1 << g2) - 1).toString(32);
    d2 >>= g2;
    e -= g2;
    rg = 1 << 32 - oc(b2) + e | c << e | d2;
    sg = f2 + a;
  } else rg = 1 << f2 | c << e | d2, sg = a;
}
function vg(a) {
  null !== a.return && (tg(a, 1), ug(a, 1, 0));
}
function wg(a) {
  for (; a === mg; ) mg = kg[--lg], kg[lg] = null, ng = kg[--lg], kg[lg] = null;
  for (; a === qg; ) qg = og[--pg], og[pg] = null, sg = og[--pg], og[pg] = null, rg = og[--pg], og[pg] = null;
}
var xg = null, yg = null, I$1 = false, zg = null;
function Ag(a, b2) {
  var c = Bg(5, null, null, 0);
  c.elementType = "DELETED";
  c.stateNode = b2;
  c.return = a;
  b2 = a.deletions;
  null === b2 ? (a.deletions = [c], a.flags |= 16) : b2.push(c);
}
function Cg(a, b2) {
  switch (a.tag) {
    case 5:
      var c = a.type;
      b2 = 1 !== b2.nodeType || c.toLowerCase() !== b2.nodeName.toLowerCase() ? null : b2;
      return null !== b2 ? (a.stateNode = b2, xg = a, yg = Lf(b2.firstChild), true) : false;
    case 6:
      return b2 = "" === a.pendingProps || 3 !== b2.nodeType ? null : b2, null !== b2 ? (a.stateNode = b2, xg = a, yg = null, true) : false;
    case 13:
      return b2 = 8 !== b2.nodeType ? null : b2, null !== b2 ? (c = null !== qg ? { id: rg, overflow: sg } : null, a.memoizedState = { dehydrated: b2, treeContext: c, retryLane: 1073741824 }, c = Bg(18, null, null, 0), c.stateNode = b2, c.return = a, a.child = c, xg = a, yg = null, true) : false;
    default:
      return false;
  }
}
function Dg(a) {
  return 0 !== (a.mode & 1) && 0 === (a.flags & 128);
}
function Eg(a) {
  if (I$1) {
    var b2 = yg;
    if (b2) {
      var c = b2;
      if (!Cg(a, b2)) {
        if (Dg(a)) throw Error(p(418));
        b2 = Lf(c.nextSibling);
        var d2 = xg;
        b2 && Cg(a, b2) ? Ag(d2, c) : (a.flags = a.flags & -4097 | 2, I$1 = false, xg = a);
      }
    } else {
      if (Dg(a)) throw Error(p(418));
      a.flags = a.flags & -4097 | 2;
      I$1 = false;
      xg = a;
    }
  }
}
function Fg(a) {
  for (a = a.return; null !== a && 5 !== a.tag && 3 !== a.tag && 13 !== a.tag; ) a = a.return;
  xg = a;
}
function Gg(a) {
  if (a !== xg) return false;
  if (!I$1) return Fg(a), I$1 = true, false;
  var b2;
  (b2 = 3 !== a.tag) && !(b2 = 5 !== a.tag) && (b2 = a.type, b2 = "head" !== b2 && "body" !== b2 && !Ef(a.type, a.memoizedProps));
  if (b2 && (b2 = yg)) {
    if (Dg(a)) throw Hg(), Error(p(418));
    for (; b2; ) Ag(a, b2), b2 = Lf(b2.nextSibling);
  }
  Fg(a);
  if (13 === a.tag) {
    a = a.memoizedState;
    a = null !== a ? a.dehydrated : null;
    if (!a) throw Error(p(317));
    a: {
      a = a.nextSibling;
      for (b2 = 0; a; ) {
        if (8 === a.nodeType) {
          var c = a.data;
          if ("/$" === c) {
            if (0 === b2) {
              yg = Lf(a.nextSibling);
              break a;
            }
            b2--;
          } else "$" !== c && "$!" !== c && "$?" !== c || b2++;
        }
        a = a.nextSibling;
      }
      yg = null;
    }
  } else yg = xg ? Lf(a.stateNode.nextSibling) : null;
  return true;
}
function Hg() {
  for (var a = yg; a; ) a = Lf(a.nextSibling);
}
function Ig() {
  yg = xg = null;
  I$1 = false;
}
function Jg(a) {
  null === zg ? zg = [a] : zg.push(a);
}
var Kg = ua.ReactCurrentBatchConfig;
function Lg(a, b2, c) {
  a = c.ref;
  if (null !== a && "function" !== typeof a && "object" !== typeof a) {
    if (c._owner) {
      c = c._owner;
      if (c) {
        if (1 !== c.tag) throw Error(p(309));
        var d2 = c.stateNode;
      }
      if (!d2) throw Error(p(147, a));
      var e = d2, f2 = "" + a;
      if (null !== b2 && null !== b2.ref && "function" === typeof b2.ref && b2.ref._stringRef === f2) return b2.ref;
      b2 = function(a2) {
        var b3 = e.refs;
        null === a2 ? delete b3[f2] : b3[f2] = a2;
      };
      b2._stringRef = f2;
      return b2;
    }
    if ("string" !== typeof a) throw Error(p(284));
    if (!c._owner) throw Error(p(290, a));
  }
  return a;
}
function Mg(a, b2) {
  a = Object.prototype.toString.call(b2);
  throw Error(p(31, "[object Object]" === a ? "object with keys {" + Object.keys(b2).join(", ") + "}" : a));
}
function Ng(a) {
  var b2 = a._init;
  return b2(a._payload);
}
function Og(a) {
  function b2(b3, c2) {
    if (a) {
      var d3 = b3.deletions;
      null === d3 ? (b3.deletions = [c2], b3.flags |= 16) : d3.push(c2);
    }
  }
  function c(c2, d3) {
    if (!a) return null;
    for (; null !== d3; ) b2(c2, d3), d3 = d3.sibling;
    return null;
  }
  function d2(a2, b3) {
    for (a2 = /* @__PURE__ */ new Map(); null !== b3; ) null !== b3.key ? a2.set(b3.key, b3) : a2.set(b3.index, b3), b3 = b3.sibling;
    return a2;
  }
  function e(a2, b3) {
    a2 = Pg(a2, b3);
    a2.index = 0;
    a2.sibling = null;
    return a2;
  }
  function f2(b3, c2, d3) {
    b3.index = d3;
    if (!a) return b3.flags |= 1048576, c2;
    d3 = b3.alternate;
    if (null !== d3) return d3 = d3.index, d3 < c2 ? (b3.flags |= 2, c2) : d3;
    b3.flags |= 2;
    return c2;
  }
  function g2(b3) {
    a && null === b3.alternate && (b3.flags |= 2);
    return b3;
  }
  function h(a2, b3, c2, d3) {
    if (null === b3 || 6 !== b3.tag) return b3 = Qg(c2, a2.mode, d3), b3.return = a2, b3;
    b3 = e(b3, c2);
    b3.return = a2;
    return b3;
  }
  function k2(a2, b3, c2, d3) {
    var f3 = c2.type;
    if (f3 === ya) return m2(a2, b3, c2.props.children, d3, c2.key);
    if (null !== b3 && (b3.elementType === f3 || "object" === typeof f3 && null !== f3 && f3.$$typeof === Ha && Ng(f3) === b3.type)) return d3 = e(b3, c2.props), d3.ref = Lg(a2, b3, c2), d3.return = a2, d3;
    d3 = Rg(c2.type, c2.key, c2.props, null, a2.mode, d3);
    d3.ref = Lg(a2, b3, c2);
    d3.return = a2;
    return d3;
  }
  function l4(a2, b3, c2, d3) {
    if (null === b3 || 4 !== b3.tag || b3.stateNode.containerInfo !== c2.containerInfo || b3.stateNode.implementation !== c2.implementation) return b3 = Sg(c2, a2.mode, d3), b3.return = a2, b3;
    b3 = e(b3, c2.children || []);
    b3.return = a2;
    return b3;
  }
  function m2(a2, b3, c2, d3, f3) {
    if (null === b3 || 7 !== b3.tag) return b3 = Tg(c2, a2.mode, d3, f3), b3.return = a2, b3;
    b3 = e(b3, c2);
    b3.return = a2;
    return b3;
  }
  function q2(a2, b3, c2) {
    if ("string" === typeof b3 && "" !== b3 || "number" === typeof b3) return b3 = Qg("" + b3, a2.mode, c2), b3.return = a2, b3;
    if ("object" === typeof b3 && null !== b3) {
      switch (b3.$$typeof) {
        case va:
          return c2 = Rg(b3.type, b3.key, b3.props, null, a2.mode, c2), c2.ref = Lg(a2, null, b3), c2.return = a2, c2;
        case wa:
          return b3 = Sg(b3, a2.mode, c2), b3.return = a2, b3;
        case Ha:
          var d3 = b3._init;
          return q2(a2, d3(b3._payload), c2);
      }
      if (eb(b3) || Ka(b3)) return b3 = Tg(b3, a2.mode, c2, null), b3.return = a2, b3;
      Mg(a2, b3);
    }
    return null;
  }
  function r2(a2, b3, c2, d3) {
    var e2 = null !== b3 ? b3.key : null;
    if ("string" === typeof c2 && "" !== c2 || "number" === typeof c2) return null !== e2 ? null : h(a2, b3, "" + c2, d3);
    if ("object" === typeof c2 && null !== c2) {
      switch (c2.$$typeof) {
        case va:
          return c2.key === e2 ? k2(a2, b3, c2, d3) : null;
        case wa:
          return c2.key === e2 ? l4(a2, b3, c2, d3) : null;
        case Ha:
          return e2 = c2._init, r2(
            a2,
            b3,
            e2(c2._payload),
            d3
          );
      }
      if (eb(c2) || Ka(c2)) return null !== e2 ? null : m2(a2, b3, c2, d3, null);
      Mg(a2, c2);
    }
    return null;
  }
  function y2(a2, b3, c2, d3, e2) {
    if ("string" === typeof d3 && "" !== d3 || "number" === typeof d3) return a2 = a2.get(c2) || null, h(b3, a2, "" + d3, e2);
    if ("object" === typeof d3 && null !== d3) {
      switch (d3.$$typeof) {
        case va:
          return a2 = a2.get(null === d3.key ? c2 : d3.key) || null, k2(b3, a2, d3, e2);
        case wa:
          return a2 = a2.get(null === d3.key ? c2 : d3.key) || null, l4(b3, a2, d3, e2);
        case Ha:
          var f3 = d3._init;
          return y2(a2, b3, c2, f3(d3._payload), e2);
      }
      if (eb(d3) || Ka(d3)) return a2 = a2.get(c2) || null, m2(b3, a2, d3, e2, null);
      Mg(b3, d3);
    }
    return null;
  }
  function n2(e2, g3, h2, k3) {
    for (var l5 = null, m3 = null, u2 = g3, w2 = g3 = 0, x2 = null; null !== u2 && w2 < h2.length; w2++) {
      u2.index > w2 ? (x2 = u2, u2 = null) : x2 = u2.sibling;
      var n3 = r2(e2, u2, h2[w2], k3);
      if (null === n3) {
        null === u2 && (u2 = x2);
        break;
      }
      a && u2 && null === n3.alternate && b2(e2, u2);
      g3 = f2(n3, g3, w2);
      null === m3 ? l5 = n3 : m3.sibling = n3;
      m3 = n3;
      u2 = x2;
    }
    if (w2 === h2.length) return c(e2, u2), I$1 && tg(e2, w2), l5;
    if (null === u2) {
      for (; w2 < h2.length; w2++) u2 = q2(e2, h2[w2], k3), null !== u2 && (g3 = f2(u2, g3, w2), null === m3 ? l5 = u2 : m3.sibling = u2, m3 = u2);
      I$1 && tg(e2, w2);
      return l5;
    }
    for (u2 = d2(e2, u2); w2 < h2.length; w2++) x2 = y2(u2, e2, w2, h2[w2], k3), null !== x2 && (a && null !== x2.alternate && u2.delete(null === x2.key ? w2 : x2.key), g3 = f2(x2, g3, w2), null === m3 ? l5 = x2 : m3.sibling = x2, m3 = x2);
    a && u2.forEach(function(a2) {
      return b2(e2, a2);
    });
    I$1 && tg(e2, w2);
    return l5;
  }
  function t2(e2, g3, h2, k3) {
    var l5 = Ka(h2);
    if ("function" !== typeof l5) throw Error(p(150));
    h2 = l5.call(h2);
    if (null == h2) throw Error(p(151));
    for (var u2 = l5 = null, m3 = g3, w2 = g3 = 0, x2 = null, n3 = h2.next(); null !== m3 && !n3.done; w2++, n3 = h2.next()) {
      m3.index > w2 ? (x2 = m3, m3 = null) : x2 = m3.sibling;
      var t3 = r2(e2, m3, n3.value, k3);
      if (null === t3) {
        null === m3 && (m3 = x2);
        break;
      }
      a && m3 && null === t3.alternate && b2(e2, m3);
      g3 = f2(t3, g3, w2);
      null === u2 ? l5 = t3 : u2.sibling = t3;
      u2 = t3;
      m3 = x2;
    }
    if (n3.done) return c(
      e2,
      m3
    ), I$1 && tg(e2, w2), l5;
    if (null === m3) {
      for (; !n3.done; w2++, n3 = h2.next()) n3 = q2(e2, n3.value, k3), null !== n3 && (g3 = f2(n3, g3, w2), null === u2 ? l5 = n3 : u2.sibling = n3, u2 = n3);
      I$1 && tg(e2, w2);
      return l5;
    }
    for (m3 = d2(e2, m3); !n3.done; w2++, n3 = h2.next()) n3 = y2(m3, e2, w2, n3.value, k3), null !== n3 && (a && null !== n3.alternate && m3.delete(null === n3.key ? w2 : n3.key), g3 = f2(n3, g3, w2), null === u2 ? l5 = n3 : u2.sibling = n3, u2 = n3);
    a && m3.forEach(function(a2) {
      return b2(e2, a2);
    });
    I$1 && tg(e2, w2);
    return l5;
  }
  function J2(a2, d3, f3, h2) {
    "object" === typeof f3 && null !== f3 && f3.type === ya && null === f3.key && (f3 = f3.props.children);
    if ("object" === typeof f3 && null !== f3) {
      switch (f3.$$typeof) {
        case va:
          a: {
            for (var k3 = f3.key, l5 = d3; null !== l5; ) {
              if (l5.key === k3) {
                k3 = f3.type;
                if (k3 === ya) {
                  if (7 === l5.tag) {
                    c(a2, l5.sibling);
                    d3 = e(l5, f3.props.children);
                    d3.return = a2;
                    a2 = d3;
                    break a;
                  }
                } else if (l5.elementType === k3 || "object" === typeof k3 && null !== k3 && k3.$$typeof === Ha && Ng(k3) === l5.type) {
                  c(a2, l5.sibling);
                  d3 = e(l5, f3.props);
                  d3.ref = Lg(a2, l5, f3);
                  d3.return = a2;
                  a2 = d3;
                  break a;
                }
                c(a2, l5);
                break;
              } else b2(a2, l5);
              l5 = l5.sibling;
            }
            f3.type === ya ? (d3 = Tg(f3.props.children, a2.mode, h2, f3.key), d3.return = a2, a2 = d3) : (h2 = Rg(f3.type, f3.key, f3.props, null, a2.mode, h2), h2.ref = Lg(a2, d3, f3), h2.return = a2, a2 = h2);
          }
          return g2(a2);
        case wa:
          a: {
            for (l5 = f3.key; null !== d3; ) {
              if (d3.key === l5) if (4 === d3.tag && d3.stateNode.containerInfo === f3.containerInfo && d3.stateNode.implementation === f3.implementation) {
                c(a2, d3.sibling);
                d3 = e(d3, f3.children || []);
                d3.return = a2;
                a2 = d3;
                break a;
              } else {
                c(a2, d3);
                break;
              }
              else b2(a2, d3);
              d3 = d3.sibling;
            }
            d3 = Sg(f3, a2.mode, h2);
            d3.return = a2;
            a2 = d3;
          }
          return g2(a2);
        case Ha:
          return l5 = f3._init, J2(a2, d3, l5(f3._payload), h2);
      }
      if (eb(f3)) return n2(a2, d3, f3, h2);
      if (Ka(f3)) return t2(a2, d3, f3, h2);
      Mg(a2, f3);
    }
    return "string" === typeof f3 && "" !== f3 || "number" === typeof f3 ? (f3 = "" + f3, null !== d3 && 6 === d3.tag ? (c(a2, d3.sibling), d3 = e(d3, f3), d3.return = a2, a2 = d3) : (c(a2, d3), d3 = Qg(f3, a2.mode, h2), d3.return = a2, a2 = d3), g2(a2)) : c(a2, d3);
  }
  return J2;
}
var Ug = Og(true), Vg = Og(false), Wg = Uf(null), Xg = null, Yg = null, Zg = null;
function $g() {
  Zg = Yg = Xg = null;
}
function ah(a) {
  var b2 = Wg.current;
  E$1(Wg);
  a._currentValue = b2;
}
function bh(a, b2, c) {
  for (; null !== a; ) {
    var d2 = a.alternate;
    (a.childLanes & b2) !== b2 ? (a.childLanes |= b2, null !== d2 && (d2.childLanes |= b2)) : null !== d2 && (d2.childLanes & b2) !== b2 && (d2.childLanes |= b2);
    if (a === c) break;
    a = a.return;
  }
}
function ch(a, b2) {
  Xg = a;
  Zg = Yg = null;
  a = a.dependencies;
  null !== a && null !== a.firstContext && (0 !== (a.lanes & b2) && (dh = true), a.firstContext = null);
}
function eh(a) {
  var b2 = a._currentValue;
  if (Zg !== a) if (a = { context: a, memoizedValue: b2, next: null }, null === Yg) {
    if (null === Xg) throw Error(p(308));
    Yg = a;
    Xg.dependencies = { lanes: 0, firstContext: a };
  } else Yg = Yg.next = a;
  return b2;
}
var fh = null;
function gh(a) {
  null === fh ? fh = [a] : fh.push(a);
}
function hh(a, b2, c, d2) {
  var e = b2.interleaved;
  null === e ? (c.next = c, gh(b2)) : (c.next = e.next, e.next = c);
  b2.interleaved = c;
  return ih(a, d2);
}
function ih(a, b2) {
  a.lanes |= b2;
  var c = a.alternate;
  null !== c && (c.lanes |= b2);
  c = a;
  for (a = a.return; null !== a; ) a.childLanes |= b2, c = a.alternate, null !== c && (c.childLanes |= b2), c = a, a = a.return;
  return 3 === c.tag ? c.stateNode : null;
}
var jh = false;
function kh(a) {
  a.updateQueue = { baseState: a.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
}
function lh(a, b2) {
  a = a.updateQueue;
  b2.updateQueue === a && (b2.updateQueue = { baseState: a.baseState, firstBaseUpdate: a.firstBaseUpdate, lastBaseUpdate: a.lastBaseUpdate, shared: a.shared, effects: a.effects });
}
function mh(a, b2) {
  return { eventTime: a, lane: b2, tag: 0, payload: null, callback: null, next: null };
}
function nh(a, b2, c) {
  var d2 = a.updateQueue;
  if (null === d2) return null;
  d2 = d2.shared;
  if (0 !== (K$1 & 2)) {
    var e = d2.pending;
    null === e ? b2.next = b2 : (b2.next = e.next, e.next = b2);
    d2.pending = b2;
    return ih(a, c);
  }
  e = d2.interleaved;
  null === e ? (b2.next = b2, gh(d2)) : (b2.next = e.next, e.next = b2);
  d2.interleaved = b2;
  return ih(a, c);
}
function oh(a, b2, c) {
  b2 = b2.updateQueue;
  if (null !== b2 && (b2 = b2.shared, 0 !== (c & 4194240))) {
    var d2 = b2.lanes;
    d2 &= a.pendingLanes;
    c |= d2;
    b2.lanes = c;
    Cc(a, c);
  }
}
function ph(a, b2) {
  var c = a.updateQueue, d2 = a.alternate;
  if (null !== d2 && (d2 = d2.updateQueue, c === d2)) {
    var e = null, f2 = null;
    c = c.firstBaseUpdate;
    if (null !== c) {
      do {
        var g2 = { eventTime: c.eventTime, lane: c.lane, tag: c.tag, payload: c.payload, callback: c.callback, next: null };
        null === f2 ? e = f2 = g2 : f2 = f2.next = g2;
        c = c.next;
      } while (null !== c);
      null === f2 ? e = f2 = b2 : f2 = f2.next = b2;
    } else e = f2 = b2;
    c = { baseState: d2.baseState, firstBaseUpdate: e, lastBaseUpdate: f2, shared: d2.shared, effects: d2.effects };
    a.updateQueue = c;
    return;
  }
  a = c.lastBaseUpdate;
  null === a ? c.firstBaseUpdate = b2 : a.next = b2;
  c.lastBaseUpdate = b2;
}
function qh(a, b2, c, d2) {
  var e = a.updateQueue;
  jh = false;
  var f2 = e.firstBaseUpdate, g2 = e.lastBaseUpdate, h = e.shared.pending;
  if (null !== h) {
    e.shared.pending = null;
    var k2 = h, l4 = k2.next;
    k2.next = null;
    null === g2 ? f2 = l4 : g2.next = l4;
    g2 = k2;
    var m2 = a.alternate;
    null !== m2 && (m2 = m2.updateQueue, h = m2.lastBaseUpdate, h !== g2 && (null === h ? m2.firstBaseUpdate = l4 : h.next = l4, m2.lastBaseUpdate = k2));
  }
  if (null !== f2) {
    var q2 = e.baseState;
    g2 = 0;
    m2 = l4 = k2 = null;
    h = f2;
    do {
      var r2 = h.lane, y2 = h.eventTime;
      if ((d2 & r2) === r2) {
        null !== m2 && (m2 = m2.next = {
          eventTime: y2,
          lane: 0,
          tag: h.tag,
          payload: h.payload,
          callback: h.callback,
          next: null
        });
        a: {
          var n2 = a, t2 = h;
          r2 = b2;
          y2 = c;
          switch (t2.tag) {
            case 1:
              n2 = t2.payload;
              if ("function" === typeof n2) {
                q2 = n2.call(y2, q2, r2);
                break a;
              }
              q2 = n2;
              break a;
            case 3:
              n2.flags = n2.flags & -65537 | 128;
            case 0:
              n2 = t2.payload;
              r2 = "function" === typeof n2 ? n2.call(y2, q2, r2) : n2;
              if (null === r2 || void 0 === r2) break a;
              q2 = A$1({}, q2, r2);
              break a;
            case 2:
              jh = true;
          }
        }
        null !== h.callback && 0 !== h.lane && (a.flags |= 64, r2 = e.effects, null === r2 ? e.effects = [h] : r2.push(h));
      } else y2 = { eventTime: y2, lane: r2, tag: h.tag, payload: h.payload, callback: h.callback, next: null }, null === m2 ? (l4 = m2 = y2, k2 = q2) : m2 = m2.next = y2, g2 |= r2;
      h = h.next;
      if (null === h) if (h = e.shared.pending, null === h) break;
      else r2 = h, h = r2.next, r2.next = null, e.lastBaseUpdate = r2, e.shared.pending = null;
    } while (1);
    null === m2 && (k2 = q2);
    e.baseState = k2;
    e.firstBaseUpdate = l4;
    e.lastBaseUpdate = m2;
    b2 = e.shared.interleaved;
    if (null !== b2) {
      e = b2;
      do
        g2 |= e.lane, e = e.next;
      while (e !== b2);
    } else null === f2 && (e.shared.lanes = 0);
    rh |= g2;
    a.lanes = g2;
    a.memoizedState = q2;
  }
}
function sh(a, b2, c) {
  a = b2.effects;
  b2.effects = null;
  if (null !== a) for (b2 = 0; b2 < a.length; b2++) {
    var d2 = a[b2], e = d2.callback;
    if (null !== e) {
      d2.callback = null;
      d2 = c;
      if ("function" !== typeof e) throw Error(p(191, e));
      e.call(d2);
    }
  }
}
var th = {}, uh = Uf(th), vh = Uf(th), wh = Uf(th);
function xh(a) {
  if (a === th) throw Error(p(174));
  return a;
}
function yh(a, b2) {
  G(wh, b2);
  G(vh, a);
  G(uh, th);
  a = b2.nodeType;
  switch (a) {
    case 9:
    case 11:
      b2 = (b2 = b2.documentElement) ? b2.namespaceURI : lb(null, "");
      break;
    default:
      a = 8 === a ? b2.parentNode : b2, b2 = a.namespaceURI || null, a = a.tagName, b2 = lb(b2, a);
  }
  E$1(uh);
  G(uh, b2);
}
function zh() {
  E$1(uh);
  E$1(vh);
  E$1(wh);
}
function Ah(a) {
  xh(wh.current);
  var b2 = xh(uh.current);
  var c = lb(b2, a.type);
  b2 !== c && (G(vh, a), G(uh, c));
}
function Bh(a) {
  vh.current === a && (E$1(uh), E$1(vh));
}
var L$1 = Uf(0);
function Ch(a) {
  for (var b2 = a; null !== b2; ) {
    if (13 === b2.tag) {
      var c = b2.memoizedState;
      if (null !== c && (c = c.dehydrated, null === c || "$?" === c.data || "$!" === c.data)) return b2;
    } else if (19 === b2.tag && void 0 !== b2.memoizedProps.revealOrder) {
      if (0 !== (b2.flags & 128)) return b2;
    } else if (null !== b2.child) {
      b2.child.return = b2;
      b2 = b2.child;
      continue;
    }
    if (b2 === a) break;
    for (; null === b2.sibling; ) {
      if (null === b2.return || b2.return === a) return null;
      b2 = b2.return;
    }
    b2.sibling.return = b2.return;
    b2 = b2.sibling;
  }
  return null;
}
var Dh = [];
function Eh() {
  for (var a = 0; a < Dh.length; a++) Dh[a]._workInProgressVersionPrimary = null;
  Dh.length = 0;
}
var Fh = ua.ReactCurrentDispatcher, Gh = ua.ReactCurrentBatchConfig, Hh = 0, M$1 = null, N$1 = null, O$1 = null, Ih = false, Jh = false, Kh = 0, Lh = 0;
function P$1() {
  throw Error(p(321));
}
function Mh(a, b2) {
  if (null === b2) return false;
  for (var c = 0; c < b2.length && c < a.length; c++) if (!He$1(a[c], b2[c])) return false;
  return true;
}
function Nh(a, b2, c, d2, e, f2) {
  Hh = f2;
  M$1 = b2;
  b2.memoizedState = null;
  b2.updateQueue = null;
  b2.lanes = 0;
  Fh.current = null === a || null === a.memoizedState ? Oh : Ph;
  a = c(d2, e);
  if (Jh) {
    f2 = 0;
    do {
      Jh = false;
      Kh = 0;
      if (25 <= f2) throw Error(p(301));
      f2 += 1;
      O$1 = N$1 = null;
      b2.updateQueue = null;
      Fh.current = Qh;
      a = c(d2, e);
    } while (Jh);
  }
  Fh.current = Rh;
  b2 = null !== N$1 && null !== N$1.next;
  Hh = 0;
  O$1 = N$1 = M$1 = null;
  Ih = false;
  if (b2) throw Error(p(300));
  return a;
}
function Sh() {
  var a = 0 !== Kh;
  Kh = 0;
  return a;
}
function Th() {
  var a = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
  null === O$1 ? M$1.memoizedState = O$1 = a : O$1 = O$1.next = a;
  return O$1;
}
function Uh() {
  if (null === N$1) {
    var a = M$1.alternate;
    a = null !== a ? a.memoizedState : null;
  } else a = N$1.next;
  var b2 = null === O$1 ? M$1.memoizedState : O$1.next;
  if (null !== b2) O$1 = b2, N$1 = a;
  else {
    if (null === a) throw Error(p(310));
    N$1 = a;
    a = { memoizedState: N$1.memoizedState, baseState: N$1.baseState, baseQueue: N$1.baseQueue, queue: N$1.queue, next: null };
    null === O$1 ? M$1.memoizedState = O$1 = a : O$1 = O$1.next = a;
  }
  return O$1;
}
function Vh(a, b2) {
  return "function" === typeof b2 ? b2(a) : b2;
}
function Wh(a) {
  var b2 = Uh(), c = b2.queue;
  if (null === c) throw Error(p(311));
  c.lastRenderedReducer = a;
  var d2 = N$1, e = d2.baseQueue, f2 = c.pending;
  if (null !== f2) {
    if (null !== e) {
      var g2 = e.next;
      e.next = f2.next;
      f2.next = g2;
    }
    d2.baseQueue = e = f2;
    c.pending = null;
  }
  if (null !== e) {
    f2 = e.next;
    d2 = d2.baseState;
    var h = g2 = null, k2 = null, l4 = f2;
    do {
      var m2 = l4.lane;
      if ((Hh & m2) === m2) null !== k2 && (k2 = k2.next = { lane: 0, action: l4.action, hasEagerState: l4.hasEagerState, eagerState: l4.eagerState, next: null }), d2 = l4.hasEagerState ? l4.eagerState : a(d2, l4.action);
      else {
        var q2 = {
          lane: m2,
          action: l4.action,
          hasEagerState: l4.hasEagerState,
          eagerState: l4.eagerState,
          next: null
        };
        null === k2 ? (h = k2 = q2, g2 = d2) : k2 = k2.next = q2;
        M$1.lanes |= m2;
        rh |= m2;
      }
      l4 = l4.next;
    } while (null !== l4 && l4 !== f2);
    null === k2 ? g2 = d2 : k2.next = h;
    He$1(d2, b2.memoizedState) || (dh = true);
    b2.memoizedState = d2;
    b2.baseState = g2;
    b2.baseQueue = k2;
    c.lastRenderedState = d2;
  }
  a = c.interleaved;
  if (null !== a) {
    e = a;
    do
      f2 = e.lane, M$1.lanes |= f2, rh |= f2, e = e.next;
    while (e !== a);
  } else null === e && (c.lanes = 0);
  return [b2.memoizedState, c.dispatch];
}
function Xh(a) {
  var b2 = Uh(), c = b2.queue;
  if (null === c) throw Error(p(311));
  c.lastRenderedReducer = a;
  var d2 = c.dispatch, e = c.pending, f2 = b2.memoizedState;
  if (null !== e) {
    c.pending = null;
    var g2 = e = e.next;
    do
      f2 = a(f2, g2.action), g2 = g2.next;
    while (g2 !== e);
    He$1(f2, b2.memoizedState) || (dh = true);
    b2.memoizedState = f2;
    null === b2.baseQueue && (b2.baseState = f2);
    c.lastRenderedState = f2;
  }
  return [f2, d2];
}
function Yh() {
}
function Zh(a, b2) {
  var c = M$1, d2 = Uh(), e = b2(), f2 = !He$1(d2.memoizedState, e);
  f2 && (d2.memoizedState = e, dh = true);
  d2 = d2.queue;
  $h(ai.bind(null, c, d2, a), [a]);
  if (d2.getSnapshot !== b2 || f2 || null !== O$1 && O$1.memoizedState.tag & 1) {
    c.flags |= 2048;
    bi(9, ci.bind(null, c, d2, e, b2), void 0, null);
    if (null === Q$1) throw Error(p(349));
    0 !== (Hh & 30) || di(c, b2, e);
  }
  return e;
}
function di(a, b2, c) {
  a.flags |= 16384;
  a = { getSnapshot: b2, value: c };
  b2 = M$1.updateQueue;
  null === b2 ? (b2 = { lastEffect: null, stores: null }, M$1.updateQueue = b2, b2.stores = [a]) : (c = b2.stores, null === c ? b2.stores = [a] : c.push(a));
}
function ci(a, b2, c, d2) {
  b2.value = c;
  b2.getSnapshot = d2;
  ei(b2) && fi(a);
}
function ai(a, b2, c) {
  return c(function() {
    ei(b2) && fi(a);
  });
}
function ei(a) {
  var b2 = a.getSnapshot;
  a = a.value;
  try {
    var c = b2();
    return !He$1(a, c);
  } catch (d2) {
    return true;
  }
}
function fi(a) {
  var b2 = ih(a, 1);
  null !== b2 && gi(b2, a, 1, -1);
}
function hi(a) {
  var b2 = Th();
  "function" === typeof a && (a = a());
  b2.memoizedState = b2.baseState = a;
  a = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: Vh, lastRenderedState: a };
  b2.queue = a;
  a = a.dispatch = ii.bind(null, M$1, a);
  return [b2.memoizedState, a];
}
function bi(a, b2, c, d2) {
  a = { tag: a, create: b2, destroy: c, deps: d2, next: null };
  b2 = M$1.updateQueue;
  null === b2 ? (b2 = { lastEffect: null, stores: null }, M$1.updateQueue = b2, b2.lastEffect = a.next = a) : (c = b2.lastEffect, null === c ? b2.lastEffect = a.next = a : (d2 = c.next, c.next = a, a.next = d2, b2.lastEffect = a));
  return a;
}
function ji() {
  return Uh().memoizedState;
}
function ki(a, b2, c, d2) {
  var e = Th();
  M$1.flags |= a;
  e.memoizedState = bi(1 | b2, c, void 0, void 0 === d2 ? null : d2);
}
function li(a, b2, c, d2) {
  var e = Uh();
  d2 = void 0 === d2 ? null : d2;
  var f2 = void 0;
  if (null !== N$1) {
    var g2 = N$1.memoizedState;
    f2 = g2.destroy;
    if (null !== d2 && Mh(d2, g2.deps)) {
      e.memoizedState = bi(b2, c, f2, d2);
      return;
    }
  }
  M$1.flags |= a;
  e.memoizedState = bi(1 | b2, c, f2, d2);
}
function mi(a, b2) {
  return ki(8390656, 8, a, b2);
}
function $h(a, b2) {
  return li(2048, 8, a, b2);
}
function ni(a, b2) {
  return li(4, 2, a, b2);
}
function oi(a, b2) {
  return li(4, 4, a, b2);
}
function pi(a, b2) {
  if ("function" === typeof b2) return a = a(), b2(a), function() {
    b2(null);
  };
  if (null !== b2 && void 0 !== b2) return a = a(), b2.current = a, function() {
    b2.current = null;
  };
}
function qi(a, b2, c) {
  c = null !== c && void 0 !== c ? c.concat([a]) : null;
  return li(4, 4, pi.bind(null, b2, a), c);
}
function ri() {
}
function si(a, b2) {
  var c = Uh();
  b2 = void 0 === b2 ? null : b2;
  var d2 = c.memoizedState;
  if (null !== d2 && null !== b2 && Mh(b2, d2[1])) return d2[0];
  c.memoizedState = [a, b2];
  return a;
}
function ti(a, b2) {
  var c = Uh();
  b2 = void 0 === b2 ? null : b2;
  var d2 = c.memoizedState;
  if (null !== d2 && null !== b2 && Mh(b2, d2[1])) return d2[0];
  a = a();
  c.memoizedState = [a, b2];
  return a;
}
function ui(a, b2, c) {
  if (0 === (Hh & 21)) return a.baseState && (a.baseState = false, dh = true), a.memoizedState = c;
  He$1(c, b2) || (c = yc(), M$1.lanes |= c, rh |= c, a.baseState = true);
  return b2;
}
function vi(a, b2) {
  var c = C;
  C = 0 !== c && 4 > c ? c : 4;
  a(true);
  var d2 = Gh.transition;
  Gh.transition = {};
  try {
    a(false), b2();
  } finally {
    C = c, Gh.transition = d2;
  }
}
function wi() {
  return Uh().memoizedState;
}
function xi(a, b2, c) {
  var d2 = yi(a);
  c = { lane: d2, action: c, hasEagerState: false, eagerState: null, next: null };
  if (zi(a)) Ai(b2, c);
  else if (c = hh(a, b2, c, d2), null !== c) {
    var e = R();
    gi(c, a, d2, e);
    Bi(c, b2, d2);
  }
}
function ii(a, b2, c) {
  var d2 = yi(a), e = { lane: d2, action: c, hasEagerState: false, eagerState: null, next: null };
  if (zi(a)) Ai(b2, e);
  else {
    var f2 = a.alternate;
    if (0 === a.lanes && (null === f2 || 0 === f2.lanes) && (f2 = b2.lastRenderedReducer, null !== f2)) try {
      var g2 = b2.lastRenderedState, h = f2(g2, c);
      e.hasEagerState = true;
      e.eagerState = h;
      if (He$1(h, g2)) {
        var k2 = b2.interleaved;
        null === k2 ? (e.next = e, gh(b2)) : (e.next = k2.next, k2.next = e);
        b2.interleaved = e;
        return;
      }
    } catch (l4) {
    } finally {
    }
    c = hh(a, b2, e, d2);
    null !== c && (e = R(), gi(c, a, d2, e), Bi(c, b2, d2));
  }
}
function zi(a) {
  var b2 = a.alternate;
  return a === M$1 || null !== b2 && b2 === M$1;
}
function Ai(a, b2) {
  Jh = Ih = true;
  var c = a.pending;
  null === c ? b2.next = b2 : (b2.next = c.next, c.next = b2);
  a.pending = b2;
}
function Bi(a, b2, c) {
  if (0 !== (c & 4194240)) {
    var d2 = b2.lanes;
    d2 &= a.pendingLanes;
    c |= d2;
    b2.lanes = c;
    Cc(a, c);
  }
}
var Rh = { readContext: eh, useCallback: P$1, useContext: P$1, useEffect: P$1, useImperativeHandle: P$1, useInsertionEffect: P$1, useLayoutEffect: P$1, useMemo: P$1, useReducer: P$1, useRef: P$1, useState: P$1, useDebugValue: P$1, useDeferredValue: P$1, useTransition: P$1, useMutableSource: P$1, useSyncExternalStore: P$1, useId: P$1, unstable_isNewReconciler: false }, Oh = { readContext: eh, useCallback: function(a, b2) {
  Th().memoizedState = [a, void 0 === b2 ? null : b2];
  return a;
}, useContext: eh, useEffect: mi, useImperativeHandle: function(a, b2, c) {
  c = null !== c && void 0 !== c ? c.concat([a]) : null;
  return ki(
    4194308,
    4,
    pi.bind(null, b2, a),
    c
  );
}, useLayoutEffect: function(a, b2) {
  return ki(4194308, 4, a, b2);
}, useInsertionEffect: function(a, b2) {
  return ki(4, 2, a, b2);
}, useMemo: function(a, b2) {
  var c = Th();
  b2 = void 0 === b2 ? null : b2;
  a = a();
  c.memoizedState = [a, b2];
  return a;
}, useReducer: function(a, b2, c) {
  var d2 = Th();
  b2 = void 0 !== c ? c(b2) : b2;
  d2.memoizedState = d2.baseState = b2;
  a = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: a, lastRenderedState: b2 };
  d2.queue = a;
  a = a.dispatch = xi.bind(null, M$1, a);
  return [d2.memoizedState, a];
}, useRef: function(a) {
  var b2 = Th();
  a = { current: a };
  return b2.memoizedState = a;
}, useState: hi, useDebugValue: ri, useDeferredValue: function(a) {
  return Th().memoizedState = a;
}, useTransition: function() {
  var a = hi(false), b2 = a[0];
  a = vi.bind(null, a[1]);
  Th().memoizedState = a;
  return [b2, a];
}, useMutableSource: function() {
}, useSyncExternalStore: function(a, b2, c) {
  var d2 = M$1, e = Th();
  if (I$1) {
    if (void 0 === c) throw Error(p(407));
    c = c();
  } else {
    c = b2();
    if (null === Q$1) throw Error(p(349));
    0 !== (Hh & 30) || di(d2, b2, c);
  }
  e.memoizedState = c;
  var f2 = { value: c, getSnapshot: b2 };
  e.queue = f2;
  mi(ai.bind(
    null,
    d2,
    f2,
    a
  ), [a]);
  d2.flags |= 2048;
  bi(9, ci.bind(null, d2, f2, c, b2), void 0, null);
  return c;
}, useId: function() {
  var a = Th(), b2 = Q$1.identifierPrefix;
  if (I$1) {
    var c = sg;
    var d2 = rg;
    c = (d2 & ~(1 << 32 - oc(d2) - 1)).toString(32) + c;
    b2 = ":" + b2 + "R" + c;
    c = Kh++;
    0 < c && (b2 += "H" + c.toString(32));
    b2 += ":";
  } else c = Lh++, b2 = ":" + b2 + "r" + c.toString(32) + ":";
  return a.memoizedState = b2;
}, unstable_isNewReconciler: false }, Ph = {
  readContext: eh,
  useCallback: si,
  useContext: eh,
  useEffect: $h,
  useImperativeHandle: qi,
  useInsertionEffect: ni,
  useLayoutEffect: oi,
  useMemo: ti,
  useReducer: Wh,
  useRef: ji,
  useState: function() {
    return Wh(Vh);
  },
  useDebugValue: ri,
  useDeferredValue: function(a) {
    var b2 = Uh();
    return ui(b2, N$1.memoizedState, a);
  },
  useTransition: function() {
    var a = Wh(Vh)[0], b2 = Uh().memoizedState;
    return [a, b2];
  },
  useMutableSource: Yh,
  useSyncExternalStore: Zh,
  useId: wi,
  unstable_isNewReconciler: false
}, Qh = { readContext: eh, useCallback: si, useContext: eh, useEffect: $h, useImperativeHandle: qi, useInsertionEffect: ni, useLayoutEffect: oi, useMemo: ti, useReducer: Xh, useRef: ji, useState: function() {
  return Xh(Vh);
}, useDebugValue: ri, useDeferredValue: function(a) {
  var b2 = Uh();
  return null === N$1 ? b2.memoizedState = a : ui(b2, N$1.memoizedState, a);
}, useTransition: function() {
  var a = Xh(Vh)[0], b2 = Uh().memoizedState;
  return [a, b2];
}, useMutableSource: Yh, useSyncExternalStore: Zh, useId: wi, unstable_isNewReconciler: false };
function Ci(a, b2) {
  if (a && a.defaultProps) {
    b2 = A$1({}, b2);
    a = a.defaultProps;
    for (var c in a) void 0 === b2[c] && (b2[c] = a[c]);
    return b2;
  }
  return b2;
}
function Di(a, b2, c, d2) {
  b2 = a.memoizedState;
  c = c(d2, b2);
  c = null === c || void 0 === c ? b2 : A$1({}, b2, c);
  a.memoizedState = c;
  0 === a.lanes && (a.updateQueue.baseState = c);
}
var Ei = { isMounted: function(a) {
  return (a = a._reactInternals) ? Vb(a) === a : false;
}, enqueueSetState: function(a, b2, c) {
  a = a._reactInternals;
  var d2 = R(), e = yi(a), f2 = mh(d2, e);
  f2.payload = b2;
  void 0 !== c && null !== c && (f2.callback = c);
  b2 = nh(a, f2, e);
  null !== b2 && (gi(b2, a, e, d2), oh(b2, a, e));
}, enqueueReplaceState: function(a, b2, c) {
  a = a._reactInternals;
  var d2 = R(), e = yi(a), f2 = mh(d2, e);
  f2.tag = 1;
  f2.payload = b2;
  void 0 !== c && null !== c && (f2.callback = c);
  b2 = nh(a, f2, e);
  null !== b2 && (gi(b2, a, e, d2), oh(b2, a, e));
}, enqueueForceUpdate: function(a, b2) {
  a = a._reactInternals;
  var c = R(), d2 = yi(a), e = mh(c, d2);
  e.tag = 2;
  void 0 !== b2 && null !== b2 && (e.callback = b2);
  b2 = nh(a, e, d2);
  null !== b2 && (gi(b2, a, d2, c), oh(b2, a, d2));
} };
function Fi(a, b2, c, d2, e, f2, g2) {
  a = a.stateNode;
  return "function" === typeof a.shouldComponentUpdate ? a.shouldComponentUpdate(d2, f2, g2) : b2.prototype && b2.prototype.isPureReactComponent ? !Ie$1(c, d2) || !Ie$1(e, f2) : true;
}
function Gi(a, b2, c) {
  var d2 = false, e = Vf;
  var f2 = b2.contextType;
  "object" === typeof f2 && null !== f2 ? f2 = eh(f2) : (e = Zf(b2) ? Xf : H$1.current, d2 = b2.contextTypes, f2 = (d2 = null !== d2 && void 0 !== d2) ? Yf(a, e) : Vf);
  b2 = new b2(c, f2);
  a.memoizedState = null !== b2.state && void 0 !== b2.state ? b2.state : null;
  b2.updater = Ei;
  a.stateNode = b2;
  b2._reactInternals = a;
  d2 && (a = a.stateNode, a.__reactInternalMemoizedUnmaskedChildContext = e, a.__reactInternalMemoizedMaskedChildContext = f2);
  return b2;
}
function Hi(a, b2, c, d2) {
  a = b2.state;
  "function" === typeof b2.componentWillReceiveProps && b2.componentWillReceiveProps(c, d2);
  "function" === typeof b2.UNSAFE_componentWillReceiveProps && b2.UNSAFE_componentWillReceiveProps(c, d2);
  b2.state !== a && Ei.enqueueReplaceState(b2, b2.state, null);
}
function Ii(a, b2, c, d2) {
  var e = a.stateNode;
  e.props = c;
  e.state = a.memoizedState;
  e.refs = {};
  kh(a);
  var f2 = b2.contextType;
  "object" === typeof f2 && null !== f2 ? e.context = eh(f2) : (f2 = Zf(b2) ? Xf : H$1.current, e.context = Yf(a, f2));
  e.state = a.memoizedState;
  f2 = b2.getDerivedStateFromProps;
  "function" === typeof f2 && (Di(a, b2, f2, c), e.state = a.memoizedState);
  "function" === typeof b2.getDerivedStateFromProps || "function" === typeof e.getSnapshotBeforeUpdate || "function" !== typeof e.UNSAFE_componentWillMount && "function" !== typeof e.componentWillMount || (b2 = e.state, "function" === typeof e.componentWillMount && e.componentWillMount(), "function" === typeof e.UNSAFE_componentWillMount && e.UNSAFE_componentWillMount(), b2 !== e.state && Ei.enqueueReplaceState(e, e.state, null), qh(a, c, e, d2), e.state = a.memoizedState);
  "function" === typeof e.componentDidMount && (a.flags |= 4194308);
}
function Ji(a, b2) {
  try {
    var c = "", d2 = b2;
    do
      c += Pa(d2), d2 = d2.return;
    while (d2);
    var e = c;
  } catch (f2) {
    e = "\nError generating stack: " + f2.message + "\n" + f2.stack;
  }
  return { value: a, source: b2, stack: e, digest: null };
}
function Ki(a, b2, c) {
  return { value: a, source: null, stack: null != c ? c : null, digest: null != b2 ? b2 : null };
}
function Li(a, b2) {
  try {
    console.error(b2.value);
  } catch (c) {
    setTimeout(function() {
      throw c;
    });
  }
}
var Mi = "function" === typeof WeakMap ? WeakMap : Map;
function Ni(a, b2, c) {
  c = mh(-1, c);
  c.tag = 3;
  c.payload = { element: null };
  var d2 = b2.value;
  c.callback = function() {
    Oi || (Oi = true, Pi = d2);
    Li(a, b2);
  };
  return c;
}
function Qi(a, b2, c) {
  c = mh(-1, c);
  c.tag = 3;
  var d2 = a.type.getDerivedStateFromError;
  if ("function" === typeof d2) {
    var e = b2.value;
    c.payload = function() {
      return d2(e);
    };
    c.callback = function() {
      Li(a, b2);
    };
  }
  var f2 = a.stateNode;
  null !== f2 && "function" === typeof f2.componentDidCatch && (c.callback = function() {
    Li(a, b2);
    "function" !== typeof d2 && (null === Ri ? Ri = /* @__PURE__ */ new Set([this]) : Ri.add(this));
    var c2 = b2.stack;
    this.componentDidCatch(b2.value, { componentStack: null !== c2 ? c2 : "" });
  });
  return c;
}
function Si(a, b2, c) {
  var d2 = a.pingCache;
  if (null === d2) {
    d2 = a.pingCache = new Mi();
    var e = /* @__PURE__ */ new Set();
    d2.set(b2, e);
  } else e = d2.get(b2), void 0 === e && (e = /* @__PURE__ */ new Set(), d2.set(b2, e));
  e.has(c) || (e.add(c), a = Ti.bind(null, a, b2, c), b2.then(a, a));
}
function Ui(a) {
  do {
    var b2;
    if (b2 = 13 === a.tag) b2 = a.memoizedState, b2 = null !== b2 ? null !== b2.dehydrated ? true : false : true;
    if (b2) return a;
    a = a.return;
  } while (null !== a);
  return null;
}
function Vi(a, b2, c, d2, e) {
  if (0 === (a.mode & 1)) return a === b2 ? a.flags |= 65536 : (a.flags |= 128, c.flags |= 131072, c.flags &= -52805, 1 === c.tag && (null === c.alternate ? c.tag = 17 : (b2 = mh(-1, 1), b2.tag = 2, nh(c, b2, 1))), c.lanes |= 1), a;
  a.flags |= 65536;
  a.lanes = e;
  return a;
}
var Wi = ua.ReactCurrentOwner, dh = false;
function Xi(a, b2, c, d2) {
  b2.child = null === a ? Vg(b2, null, c, d2) : Ug(b2, a.child, c, d2);
}
function Yi(a, b2, c, d2, e) {
  c = c.render;
  var f2 = b2.ref;
  ch(b2, e);
  d2 = Nh(a, b2, c, d2, f2, e);
  c = Sh();
  if (null !== a && !dh) return b2.updateQueue = a.updateQueue, b2.flags &= -2053, a.lanes &= ~e, Zi(a, b2, e);
  I$1 && c && vg(b2);
  b2.flags |= 1;
  Xi(a, b2, d2, e);
  return b2.child;
}
function $i(a, b2, c, d2, e) {
  if (null === a) {
    var f2 = c.type;
    if ("function" === typeof f2 && !aj(f2) && void 0 === f2.defaultProps && null === c.compare && void 0 === c.defaultProps) return b2.tag = 15, b2.type = f2, bj(a, b2, f2, d2, e);
    a = Rg(c.type, null, d2, b2, b2.mode, e);
    a.ref = b2.ref;
    a.return = b2;
    return b2.child = a;
  }
  f2 = a.child;
  if (0 === (a.lanes & e)) {
    var g2 = f2.memoizedProps;
    c = c.compare;
    c = null !== c ? c : Ie$1;
    if (c(g2, d2) && a.ref === b2.ref) return Zi(a, b2, e);
  }
  b2.flags |= 1;
  a = Pg(f2, d2);
  a.ref = b2.ref;
  a.return = b2;
  return b2.child = a;
}
function bj(a, b2, c, d2, e) {
  if (null !== a) {
    var f2 = a.memoizedProps;
    if (Ie$1(f2, d2) && a.ref === b2.ref) if (dh = false, b2.pendingProps = d2 = f2, 0 !== (a.lanes & e)) 0 !== (a.flags & 131072) && (dh = true);
    else return b2.lanes = a.lanes, Zi(a, b2, e);
  }
  return cj(a, b2, c, d2, e);
}
function dj(a, b2, c) {
  var d2 = b2.pendingProps, e = d2.children, f2 = null !== a ? a.memoizedState : null;
  if ("hidden" === d2.mode) if (0 === (b2.mode & 1)) b2.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, G(ej, fj), fj |= c;
  else {
    if (0 === (c & 1073741824)) return a = null !== f2 ? f2.baseLanes | c : c, b2.lanes = b2.childLanes = 1073741824, b2.memoizedState = { baseLanes: a, cachePool: null, transitions: null }, b2.updateQueue = null, G(ej, fj), fj |= a, null;
    b2.memoizedState = { baseLanes: 0, cachePool: null, transitions: null };
    d2 = null !== f2 ? f2.baseLanes : c;
    G(ej, fj);
    fj |= d2;
  }
  else null !== f2 ? (d2 = f2.baseLanes | c, b2.memoizedState = null) : d2 = c, G(ej, fj), fj |= d2;
  Xi(a, b2, e, c);
  return b2.child;
}
function gj(a, b2) {
  var c = b2.ref;
  if (null === a && null !== c || null !== a && a.ref !== c) b2.flags |= 512, b2.flags |= 2097152;
}
function cj(a, b2, c, d2, e) {
  var f2 = Zf(c) ? Xf : H$1.current;
  f2 = Yf(b2, f2);
  ch(b2, e);
  c = Nh(a, b2, c, d2, f2, e);
  d2 = Sh();
  if (null !== a && !dh) return b2.updateQueue = a.updateQueue, b2.flags &= -2053, a.lanes &= ~e, Zi(a, b2, e);
  I$1 && d2 && vg(b2);
  b2.flags |= 1;
  Xi(a, b2, c, e);
  return b2.child;
}
function hj(a, b2, c, d2, e) {
  if (Zf(c)) {
    var f2 = true;
    cg(b2);
  } else f2 = false;
  ch(b2, e);
  if (null === b2.stateNode) ij(a, b2), Gi(b2, c, d2), Ii(b2, c, d2, e), d2 = true;
  else if (null === a) {
    var g2 = b2.stateNode, h = b2.memoizedProps;
    g2.props = h;
    var k2 = g2.context, l4 = c.contextType;
    "object" === typeof l4 && null !== l4 ? l4 = eh(l4) : (l4 = Zf(c) ? Xf : H$1.current, l4 = Yf(b2, l4));
    var m2 = c.getDerivedStateFromProps, q2 = "function" === typeof m2 || "function" === typeof g2.getSnapshotBeforeUpdate;
    q2 || "function" !== typeof g2.UNSAFE_componentWillReceiveProps && "function" !== typeof g2.componentWillReceiveProps || (h !== d2 || k2 !== l4) && Hi(b2, g2, d2, l4);
    jh = false;
    var r2 = b2.memoizedState;
    g2.state = r2;
    qh(b2, d2, g2, e);
    k2 = b2.memoizedState;
    h !== d2 || r2 !== k2 || Wf.current || jh ? ("function" === typeof m2 && (Di(b2, c, m2, d2), k2 = b2.memoizedState), (h = jh || Fi(b2, c, h, d2, r2, k2, l4)) ? (q2 || "function" !== typeof g2.UNSAFE_componentWillMount && "function" !== typeof g2.componentWillMount || ("function" === typeof g2.componentWillMount && g2.componentWillMount(), "function" === typeof g2.UNSAFE_componentWillMount && g2.UNSAFE_componentWillMount()), "function" === typeof g2.componentDidMount && (b2.flags |= 4194308)) : ("function" === typeof g2.componentDidMount && (b2.flags |= 4194308), b2.memoizedProps = d2, b2.memoizedState = k2), g2.props = d2, g2.state = k2, g2.context = l4, d2 = h) : ("function" === typeof g2.componentDidMount && (b2.flags |= 4194308), d2 = false);
  } else {
    g2 = b2.stateNode;
    lh(a, b2);
    h = b2.memoizedProps;
    l4 = b2.type === b2.elementType ? h : Ci(b2.type, h);
    g2.props = l4;
    q2 = b2.pendingProps;
    r2 = g2.context;
    k2 = c.contextType;
    "object" === typeof k2 && null !== k2 ? k2 = eh(k2) : (k2 = Zf(c) ? Xf : H$1.current, k2 = Yf(b2, k2));
    var y2 = c.getDerivedStateFromProps;
    (m2 = "function" === typeof y2 || "function" === typeof g2.getSnapshotBeforeUpdate) || "function" !== typeof g2.UNSAFE_componentWillReceiveProps && "function" !== typeof g2.componentWillReceiveProps || (h !== q2 || r2 !== k2) && Hi(b2, g2, d2, k2);
    jh = false;
    r2 = b2.memoizedState;
    g2.state = r2;
    qh(b2, d2, g2, e);
    var n2 = b2.memoizedState;
    h !== q2 || r2 !== n2 || Wf.current || jh ? ("function" === typeof y2 && (Di(b2, c, y2, d2), n2 = b2.memoizedState), (l4 = jh || Fi(b2, c, l4, d2, r2, n2, k2) || false) ? (m2 || "function" !== typeof g2.UNSAFE_componentWillUpdate && "function" !== typeof g2.componentWillUpdate || ("function" === typeof g2.componentWillUpdate && g2.componentWillUpdate(d2, n2, k2), "function" === typeof g2.UNSAFE_componentWillUpdate && g2.UNSAFE_componentWillUpdate(d2, n2, k2)), "function" === typeof g2.componentDidUpdate && (b2.flags |= 4), "function" === typeof g2.getSnapshotBeforeUpdate && (b2.flags |= 1024)) : ("function" !== typeof g2.componentDidUpdate || h === a.memoizedProps && r2 === a.memoizedState || (b2.flags |= 4), "function" !== typeof g2.getSnapshotBeforeUpdate || h === a.memoizedProps && r2 === a.memoizedState || (b2.flags |= 1024), b2.memoizedProps = d2, b2.memoizedState = n2), g2.props = d2, g2.state = n2, g2.context = k2, d2 = l4) : ("function" !== typeof g2.componentDidUpdate || h === a.memoizedProps && r2 === a.memoizedState || (b2.flags |= 4), "function" !== typeof g2.getSnapshotBeforeUpdate || h === a.memoizedProps && r2 === a.memoizedState || (b2.flags |= 1024), d2 = false);
  }
  return jj(a, b2, c, d2, f2, e);
}
function jj(a, b2, c, d2, e, f2) {
  gj(a, b2);
  var g2 = 0 !== (b2.flags & 128);
  if (!d2 && !g2) return e && dg(b2, c, false), Zi(a, b2, f2);
  d2 = b2.stateNode;
  Wi.current = b2;
  var h = g2 && "function" !== typeof c.getDerivedStateFromError ? null : d2.render();
  b2.flags |= 1;
  null !== a && g2 ? (b2.child = Ug(b2, a.child, null, f2), b2.child = Ug(b2, null, h, f2)) : Xi(a, b2, h, f2);
  b2.memoizedState = d2.state;
  e && dg(b2, c, true);
  return b2.child;
}
function kj(a) {
  var b2 = a.stateNode;
  b2.pendingContext ? ag(a, b2.pendingContext, b2.pendingContext !== b2.context) : b2.context && ag(a, b2.context, false);
  yh(a, b2.containerInfo);
}
function lj(a, b2, c, d2, e) {
  Ig();
  Jg(e);
  b2.flags |= 256;
  Xi(a, b2, c, d2);
  return b2.child;
}
var mj = { dehydrated: null, treeContext: null, retryLane: 0 };
function nj(a) {
  return { baseLanes: a, cachePool: null, transitions: null };
}
function oj(a, b2, c) {
  var d2 = b2.pendingProps, e = L$1.current, f2 = false, g2 = 0 !== (b2.flags & 128), h;
  (h = g2) || (h = null !== a && null === a.memoizedState ? false : 0 !== (e & 2));
  if (h) f2 = true, b2.flags &= -129;
  else if (null === a || null !== a.memoizedState) e |= 1;
  G(L$1, e & 1);
  if (null === a) {
    Eg(b2);
    a = b2.memoizedState;
    if (null !== a && (a = a.dehydrated, null !== a)) return 0 === (b2.mode & 1) ? b2.lanes = 1 : "$!" === a.data ? b2.lanes = 8 : b2.lanes = 1073741824, null;
    g2 = d2.children;
    a = d2.fallback;
    return f2 ? (d2 = b2.mode, f2 = b2.child, g2 = { mode: "hidden", children: g2 }, 0 === (d2 & 1) && null !== f2 ? (f2.childLanes = 0, f2.pendingProps = g2) : f2 = pj(g2, d2, 0, null), a = Tg(a, d2, c, null), f2.return = b2, a.return = b2, f2.sibling = a, b2.child = f2, b2.child.memoizedState = nj(c), b2.memoizedState = mj, a) : qj(b2, g2);
  }
  e = a.memoizedState;
  if (null !== e && (h = e.dehydrated, null !== h)) return rj(a, b2, g2, d2, h, e, c);
  if (f2) {
    f2 = d2.fallback;
    g2 = b2.mode;
    e = a.child;
    h = e.sibling;
    var k2 = { mode: "hidden", children: d2.children };
    0 === (g2 & 1) && b2.child !== e ? (d2 = b2.child, d2.childLanes = 0, d2.pendingProps = k2, b2.deletions = null) : (d2 = Pg(e, k2), d2.subtreeFlags = e.subtreeFlags & 14680064);
    null !== h ? f2 = Pg(h, f2) : (f2 = Tg(f2, g2, c, null), f2.flags |= 2);
    f2.return = b2;
    d2.return = b2;
    d2.sibling = f2;
    b2.child = d2;
    d2 = f2;
    f2 = b2.child;
    g2 = a.child.memoizedState;
    g2 = null === g2 ? nj(c) : { baseLanes: g2.baseLanes | c, cachePool: null, transitions: g2.transitions };
    f2.memoizedState = g2;
    f2.childLanes = a.childLanes & ~c;
    b2.memoizedState = mj;
    return d2;
  }
  f2 = a.child;
  a = f2.sibling;
  d2 = Pg(f2, { mode: "visible", children: d2.children });
  0 === (b2.mode & 1) && (d2.lanes = c);
  d2.return = b2;
  d2.sibling = null;
  null !== a && (c = b2.deletions, null === c ? (b2.deletions = [a], b2.flags |= 16) : c.push(a));
  b2.child = d2;
  b2.memoizedState = null;
  return d2;
}
function qj(a, b2) {
  b2 = pj({ mode: "visible", children: b2 }, a.mode, 0, null);
  b2.return = a;
  return a.child = b2;
}
function sj(a, b2, c, d2) {
  null !== d2 && Jg(d2);
  Ug(b2, a.child, null, c);
  a = qj(b2, b2.pendingProps.children);
  a.flags |= 2;
  b2.memoizedState = null;
  return a;
}
function rj(a, b2, c, d2, e, f2, g2) {
  if (c) {
    if (b2.flags & 256) return b2.flags &= -257, d2 = Ki(Error(p(422))), sj(a, b2, g2, d2);
    if (null !== b2.memoizedState) return b2.child = a.child, b2.flags |= 128, null;
    f2 = d2.fallback;
    e = b2.mode;
    d2 = pj({ mode: "visible", children: d2.children }, e, 0, null);
    f2 = Tg(f2, e, g2, null);
    f2.flags |= 2;
    d2.return = b2;
    f2.return = b2;
    d2.sibling = f2;
    b2.child = d2;
    0 !== (b2.mode & 1) && Ug(b2, a.child, null, g2);
    b2.child.memoizedState = nj(g2);
    b2.memoizedState = mj;
    return f2;
  }
  if (0 === (b2.mode & 1)) return sj(a, b2, g2, null);
  if ("$!" === e.data) {
    d2 = e.nextSibling && e.nextSibling.dataset;
    if (d2) var h = d2.dgst;
    d2 = h;
    f2 = Error(p(419));
    d2 = Ki(f2, d2, void 0);
    return sj(a, b2, g2, d2);
  }
  h = 0 !== (g2 & a.childLanes);
  if (dh || h) {
    d2 = Q$1;
    if (null !== d2) {
      switch (g2 & -g2) {
        case 4:
          e = 2;
          break;
        case 16:
          e = 8;
          break;
        case 64:
        case 128:
        case 256:
        case 512:
        case 1024:
        case 2048:
        case 4096:
        case 8192:
        case 16384:
        case 32768:
        case 65536:
        case 131072:
        case 262144:
        case 524288:
        case 1048576:
        case 2097152:
        case 4194304:
        case 8388608:
        case 16777216:
        case 33554432:
        case 67108864:
          e = 32;
          break;
        case 536870912:
          e = 268435456;
          break;
        default:
          e = 0;
      }
      e = 0 !== (e & (d2.suspendedLanes | g2)) ? 0 : e;
      0 !== e && e !== f2.retryLane && (f2.retryLane = e, ih(a, e), gi(d2, a, e, -1));
    }
    tj();
    d2 = Ki(Error(p(421)));
    return sj(a, b2, g2, d2);
  }
  if ("$?" === e.data) return b2.flags |= 128, b2.child = a.child, b2 = uj.bind(null, a), e._reactRetry = b2, null;
  a = f2.treeContext;
  yg = Lf(e.nextSibling);
  xg = b2;
  I$1 = true;
  zg = null;
  null !== a && (og[pg++] = rg, og[pg++] = sg, og[pg++] = qg, rg = a.id, sg = a.overflow, qg = b2);
  b2 = qj(b2, d2.children);
  b2.flags |= 4096;
  return b2;
}
function vj(a, b2, c) {
  a.lanes |= b2;
  var d2 = a.alternate;
  null !== d2 && (d2.lanes |= b2);
  bh(a.return, b2, c);
}
function wj(a, b2, c, d2, e) {
  var f2 = a.memoizedState;
  null === f2 ? a.memoizedState = { isBackwards: b2, rendering: null, renderingStartTime: 0, last: d2, tail: c, tailMode: e } : (f2.isBackwards = b2, f2.rendering = null, f2.renderingStartTime = 0, f2.last = d2, f2.tail = c, f2.tailMode = e);
}
function xj(a, b2, c) {
  var d2 = b2.pendingProps, e = d2.revealOrder, f2 = d2.tail;
  Xi(a, b2, d2.children, c);
  d2 = L$1.current;
  if (0 !== (d2 & 2)) d2 = d2 & 1 | 2, b2.flags |= 128;
  else {
    if (null !== a && 0 !== (a.flags & 128)) a: for (a = b2.child; null !== a; ) {
      if (13 === a.tag) null !== a.memoizedState && vj(a, c, b2);
      else if (19 === a.tag) vj(a, c, b2);
      else if (null !== a.child) {
        a.child.return = a;
        a = a.child;
        continue;
      }
      if (a === b2) break a;
      for (; null === a.sibling; ) {
        if (null === a.return || a.return === b2) break a;
        a = a.return;
      }
      a.sibling.return = a.return;
      a = a.sibling;
    }
    d2 &= 1;
  }
  G(L$1, d2);
  if (0 === (b2.mode & 1)) b2.memoizedState = null;
  else switch (e) {
    case "forwards":
      c = b2.child;
      for (e = null; null !== c; ) a = c.alternate, null !== a && null === Ch(a) && (e = c), c = c.sibling;
      c = e;
      null === c ? (e = b2.child, b2.child = null) : (e = c.sibling, c.sibling = null);
      wj(b2, false, e, c, f2);
      break;
    case "backwards":
      c = null;
      e = b2.child;
      for (b2.child = null; null !== e; ) {
        a = e.alternate;
        if (null !== a && null === Ch(a)) {
          b2.child = e;
          break;
        }
        a = e.sibling;
        e.sibling = c;
        c = e;
        e = a;
      }
      wj(b2, true, c, null, f2);
      break;
    case "together":
      wj(b2, false, null, null, void 0);
      break;
    default:
      b2.memoizedState = null;
  }
  return b2.child;
}
function ij(a, b2) {
  0 === (b2.mode & 1) && null !== a && (a.alternate = null, b2.alternate = null, b2.flags |= 2);
}
function Zi(a, b2, c) {
  null !== a && (b2.dependencies = a.dependencies);
  rh |= b2.lanes;
  if (0 === (c & b2.childLanes)) return null;
  if (null !== a && b2.child !== a.child) throw Error(p(153));
  if (null !== b2.child) {
    a = b2.child;
    c = Pg(a, a.pendingProps);
    b2.child = c;
    for (c.return = b2; null !== a.sibling; ) a = a.sibling, c = c.sibling = Pg(a, a.pendingProps), c.return = b2;
    c.sibling = null;
  }
  return b2.child;
}
function yj(a, b2, c) {
  switch (b2.tag) {
    case 3:
      kj(b2);
      Ig();
      break;
    case 5:
      Ah(b2);
      break;
    case 1:
      Zf(b2.type) && cg(b2);
      break;
    case 4:
      yh(b2, b2.stateNode.containerInfo);
      break;
    case 10:
      var d2 = b2.type._context, e = b2.memoizedProps.value;
      G(Wg, d2._currentValue);
      d2._currentValue = e;
      break;
    case 13:
      d2 = b2.memoizedState;
      if (null !== d2) {
        if (null !== d2.dehydrated) return G(L$1, L$1.current & 1), b2.flags |= 128, null;
        if (0 !== (c & b2.child.childLanes)) return oj(a, b2, c);
        G(L$1, L$1.current & 1);
        a = Zi(a, b2, c);
        return null !== a ? a.sibling : null;
      }
      G(L$1, L$1.current & 1);
      break;
    case 19:
      d2 = 0 !== (c & b2.childLanes);
      if (0 !== (a.flags & 128)) {
        if (d2) return xj(a, b2, c);
        b2.flags |= 128;
      }
      e = b2.memoizedState;
      null !== e && (e.rendering = null, e.tail = null, e.lastEffect = null);
      G(L$1, L$1.current);
      if (d2) break;
      else return null;
    case 22:
    case 23:
      return b2.lanes = 0, dj(a, b2, c);
  }
  return Zi(a, b2, c);
}
var zj, Aj, Bj, Cj;
zj = function(a, b2) {
  for (var c = b2.child; null !== c; ) {
    if (5 === c.tag || 6 === c.tag) a.appendChild(c.stateNode);
    else if (4 !== c.tag && null !== c.child) {
      c.child.return = c;
      c = c.child;
      continue;
    }
    if (c === b2) break;
    for (; null === c.sibling; ) {
      if (null === c.return || c.return === b2) return;
      c = c.return;
    }
    c.sibling.return = c.return;
    c = c.sibling;
  }
};
Aj = function() {
};
Bj = function(a, b2, c, d2) {
  var e = a.memoizedProps;
  if (e !== d2) {
    a = b2.stateNode;
    xh(uh.current);
    var f2 = null;
    switch (c) {
      case "input":
        e = Ya(a, e);
        d2 = Ya(a, d2);
        f2 = [];
        break;
      case "select":
        e = A$1({}, e, { value: void 0 });
        d2 = A$1({}, d2, { value: void 0 });
        f2 = [];
        break;
      case "textarea":
        e = gb(a, e);
        d2 = gb(a, d2);
        f2 = [];
        break;
      default:
        "function" !== typeof e.onClick && "function" === typeof d2.onClick && (a.onclick = Bf);
    }
    ub(c, d2);
    var g2;
    c = null;
    for (l4 in e) if (!d2.hasOwnProperty(l4) && e.hasOwnProperty(l4) && null != e[l4]) if ("style" === l4) {
      var h = e[l4];
      for (g2 in h) h.hasOwnProperty(g2) && (c || (c = {}), c[g2] = "");
    } else "dangerouslySetInnerHTML" !== l4 && "children" !== l4 && "suppressContentEditableWarning" !== l4 && "suppressHydrationWarning" !== l4 && "autoFocus" !== l4 && (ea.hasOwnProperty(l4) ? f2 || (f2 = []) : (f2 = f2 || []).push(l4, null));
    for (l4 in d2) {
      var k2 = d2[l4];
      h = null != e ? e[l4] : void 0;
      if (d2.hasOwnProperty(l4) && k2 !== h && (null != k2 || null != h)) if ("style" === l4) if (h) {
        for (g2 in h) !h.hasOwnProperty(g2) || k2 && k2.hasOwnProperty(g2) || (c || (c = {}), c[g2] = "");
        for (g2 in k2) k2.hasOwnProperty(g2) && h[g2] !== k2[g2] && (c || (c = {}), c[g2] = k2[g2]);
      } else c || (f2 || (f2 = []), f2.push(
        l4,
        c
      )), c = k2;
      else "dangerouslySetInnerHTML" === l4 ? (k2 = k2 ? k2.__html : void 0, h = h ? h.__html : void 0, null != k2 && h !== k2 && (f2 = f2 || []).push(l4, k2)) : "children" === l4 ? "string" !== typeof k2 && "number" !== typeof k2 || (f2 = f2 || []).push(l4, "" + k2) : "suppressContentEditableWarning" !== l4 && "suppressHydrationWarning" !== l4 && (ea.hasOwnProperty(l4) ? (null != k2 && "onScroll" === l4 && D$1("scroll", a), f2 || h === k2 || (f2 = [])) : (f2 = f2 || []).push(l4, k2));
    }
    c && (f2 = f2 || []).push("style", c);
    var l4 = f2;
    if (b2.updateQueue = l4) b2.flags |= 4;
  }
};
Cj = function(a, b2, c, d2) {
  c !== d2 && (b2.flags |= 4);
};
function Dj(a, b2) {
  if (!I$1) switch (a.tailMode) {
    case "hidden":
      b2 = a.tail;
      for (var c = null; null !== b2; ) null !== b2.alternate && (c = b2), b2 = b2.sibling;
      null === c ? a.tail = null : c.sibling = null;
      break;
    case "collapsed":
      c = a.tail;
      for (var d2 = null; null !== c; ) null !== c.alternate && (d2 = c), c = c.sibling;
      null === d2 ? b2 || null === a.tail ? a.tail = null : a.tail.sibling = null : d2.sibling = null;
  }
}
function S(a) {
  var b2 = null !== a.alternate && a.alternate.child === a.child, c = 0, d2 = 0;
  if (b2) for (var e = a.child; null !== e; ) c |= e.lanes | e.childLanes, d2 |= e.subtreeFlags & 14680064, d2 |= e.flags & 14680064, e.return = a, e = e.sibling;
  else for (e = a.child; null !== e; ) c |= e.lanes | e.childLanes, d2 |= e.subtreeFlags, d2 |= e.flags, e.return = a, e = e.sibling;
  a.subtreeFlags |= d2;
  a.childLanes = c;
  return b2;
}
function Ej(a, b2, c) {
  var d2 = b2.pendingProps;
  wg(b2);
  switch (b2.tag) {
    case 2:
    case 16:
    case 15:
    case 0:
    case 11:
    case 7:
    case 8:
    case 12:
    case 9:
    case 14:
      return S(b2), null;
    case 1:
      return Zf(b2.type) && $f(), S(b2), null;
    case 3:
      d2 = b2.stateNode;
      zh();
      E$1(Wf);
      E$1(H$1);
      Eh();
      d2.pendingContext && (d2.context = d2.pendingContext, d2.pendingContext = null);
      if (null === a || null === a.child) Gg(b2) ? b2.flags |= 4 : null === a || a.memoizedState.isDehydrated && 0 === (b2.flags & 256) || (b2.flags |= 1024, null !== zg && (Fj(zg), zg = null));
      Aj(a, b2);
      S(b2);
      return null;
    case 5:
      Bh(b2);
      var e = xh(wh.current);
      c = b2.type;
      if (null !== a && null != b2.stateNode) Bj(a, b2, c, d2, e), a.ref !== b2.ref && (b2.flags |= 512, b2.flags |= 2097152);
      else {
        if (!d2) {
          if (null === b2.stateNode) throw Error(p(166));
          S(b2);
          return null;
        }
        a = xh(uh.current);
        if (Gg(b2)) {
          d2 = b2.stateNode;
          c = b2.type;
          var f2 = b2.memoizedProps;
          d2[Of] = b2;
          d2[Pf] = f2;
          a = 0 !== (b2.mode & 1);
          switch (c) {
            case "dialog":
              D$1("cancel", d2);
              D$1("close", d2);
              break;
            case "iframe":
            case "object":
            case "embed":
              D$1("load", d2);
              break;
            case "video":
            case "audio":
              for (e = 0; e < lf.length; e++) D$1(lf[e], d2);
              break;
            case "source":
              D$1("error", d2);
              break;
            case "img":
            case "image":
            case "link":
              D$1(
                "error",
                d2
              );
              D$1("load", d2);
              break;
            case "details":
              D$1("toggle", d2);
              break;
            case "input":
              Za(d2, f2);
              D$1("invalid", d2);
              break;
            case "select":
              d2._wrapperState = { wasMultiple: !!f2.multiple };
              D$1("invalid", d2);
              break;
            case "textarea":
              hb(d2, f2), D$1("invalid", d2);
          }
          ub(c, f2);
          e = null;
          for (var g2 in f2) if (f2.hasOwnProperty(g2)) {
            var h = f2[g2];
            "children" === g2 ? "string" === typeof h ? d2.textContent !== h && (true !== f2.suppressHydrationWarning && Af(d2.textContent, h, a), e = ["children", h]) : "number" === typeof h && d2.textContent !== "" + h && (true !== f2.suppressHydrationWarning && Af(
              d2.textContent,
              h,
              a
            ), e = ["children", "" + h]) : ea.hasOwnProperty(g2) && null != h && "onScroll" === g2 && D$1("scroll", d2);
          }
          switch (c) {
            case "input":
              Va(d2);
              db(d2, f2, true);
              break;
            case "textarea":
              Va(d2);
              jb(d2);
              break;
            case "select":
            case "option":
              break;
            default:
              "function" === typeof f2.onClick && (d2.onclick = Bf);
          }
          d2 = e;
          b2.updateQueue = d2;
          null !== d2 && (b2.flags |= 4);
        } else {
          g2 = 9 === e.nodeType ? e : e.ownerDocument;
          "http://www.w3.org/1999/xhtml" === a && (a = kb(c));
          "http://www.w3.org/1999/xhtml" === a ? "script" === c ? (a = g2.createElement("div"), a.innerHTML = "<script><\/script>", a = a.removeChild(a.firstChild)) : "string" === typeof d2.is ? a = g2.createElement(c, { is: d2.is }) : (a = g2.createElement(c), "select" === c && (g2 = a, d2.multiple ? g2.multiple = true : d2.size && (g2.size = d2.size))) : a = g2.createElementNS(a, c);
          a[Of] = b2;
          a[Pf] = d2;
          zj(a, b2, false, false);
          b2.stateNode = a;
          a: {
            g2 = vb(c, d2);
            switch (c) {
              case "dialog":
                D$1("cancel", a);
                D$1("close", a);
                e = d2;
                break;
              case "iframe":
              case "object":
              case "embed":
                D$1("load", a);
                e = d2;
                break;
              case "video":
              case "audio":
                for (e = 0; e < lf.length; e++) D$1(lf[e], a);
                e = d2;
                break;
              case "source":
                D$1("error", a);
                e = d2;
                break;
              case "img":
              case "image":
              case "link":
                D$1(
                  "error",
                  a
                );
                D$1("load", a);
                e = d2;
                break;
              case "details":
                D$1("toggle", a);
                e = d2;
                break;
              case "input":
                Za(a, d2);
                e = Ya(a, d2);
                D$1("invalid", a);
                break;
              case "option":
                e = d2;
                break;
              case "select":
                a._wrapperState = { wasMultiple: !!d2.multiple };
                e = A$1({}, d2, { value: void 0 });
                D$1("invalid", a);
                break;
              case "textarea":
                hb(a, d2);
                e = gb(a, d2);
                D$1("invalid", a);
                break;
              default:
                e = d2;
            }
            ub(c, e);
            h = e;
            for (f2 in h) if (h.hasOwnProperty(f2)) {
              var k2 = h[f2];
              "style" === f2 ? sb(a, k2) : "dangerouslySetInnerHTML" === f2 ? (k2 = k2 ? k2.__html : void 0, null != k2 && nb(a, k2)) : "children" === f2 ? "string" === typeof k2 ? ("textarea" !== c || "" !== k2) && ob(a, k2) : "number" === typeof k2 && ob(a, "" + k2) : "suppressContentEditableWarning" !== f2 && "suppressHydrationWarning" !== f2 && "autoFocus" !== f2 && (ea.hasOwnProperty(f2) ? null != k2 && "onScroll" === f2 && D$1("scroll", a) : null != k2 && ta(a, f2, k2, g2));
            }
            switch (c) {
              case "input":
                Va(a);
                db(a, d2, false);
                break;
              case "textarea":
                Va(a);
                jb(a);
                break;
              case "option":
                null != d2.value && a.setAttribute("value", "" + Sa(d2.value));
                break;
              case "select":
                a.multiple = !!d2.multiple;
                f2 = d2.value;
                null != f2 ? fb(a, !!d2.multiple, f2, false) : null != d2.defaultValue && fb(
                  a,
                  !!d2.multiple,
                  d2.defaultValue,
                  true
                );
                break;
              default:
                "function" === typeof e.onClick && (a.onclick = Bf);
            }
            switch (c) {
              case "button":
              case "input":
              case "select":
              case "textarea":
                d2 = !!d2.autoFocus;
                break a;
              case "img":
                d2 = true;
                break a;
              default:
                d2 = false;
            }
          }
          d2 && (b2.flags |= 4);
        }
        null !== b2.ref && (b2.flags |= 512, b2.flags |= 2097152);
      }
      S(b2);
      return null;
    case 6:
      if (a && null != b2.stateNode) Cj(a, b2, a.memoizedProps, d2);
      else {
        if ("string" !== typeof d2 && null === b2.stateNode) throw Error(p(166));
        c = xh(wh.current);
        xh(uh.current);
        if (Gg(b2)) {
          d2 = b2.stateNode;
          c = b2.memoizedProps;
          d2[Of] = b2;
          if (f2 = d2.nodeValue !== c) {
            if (a = xg, null !== a) switch (a.tag) {
              case 3:
                Af(d2.nodeValue, c, 0 !== (a.mode & 1));
                break;
              case 5:
                true !== a.memoizedProps.suppressHydrationWarning && Af(d2.nodeValue, c, 0 !== (a.mode & 1));
            }
          }
          f2 && (b2.flags |= 4);
        } else d2 = (9 === c.nodeType ? c : c.ownerDocument).createTextNode(d2), d2[Of] = b2, b2.stateNode = d2;
      }
      S(b2);
      return null;
    case 13:
      E$1(L$1);
      d2 = b2.memoizedState;
      if (null === a || null !== a.memoizedState && null !== a.memoizedState.dehydrated) {
        if (I$1 && null !== yg && 0 !== (b2.mode & 1) && 0 === (b2.flags & 128)) Hg(), Ig(), b2.flags |= 98560, f2 = false;
        else if (f2 = Gg(b2), null !== d2 && null !== d2.dehydrated) {
          if (null === a) {
            if (!f2) throw Error(p(318));
            f2 = b2.memoizedState;
            f2 = null !== f2 ? f2.dehydrated : null;
            if (!f2) throw Error(p(317));
            f2[Of] = b2;
          } else Ig(), 0 === (b2.flags & 128) && (b2.memoizedState = null), b2.flags |= 4;
          S(b2);
          f2 = false;
        } else null !== zg && (Fj(zg), zg = null), f2 = true;
        if (!f2) return b2.flags & 65536 ? b2 : null;
      }
      if (0 !== (b2.flags & 128)) return b2.lanes = c, b2;
      d2 = null !== d2;
      d2 !== (null !== a && null !== a.memoizedState) && d2 && (b2.child.flags |= 8192, 0 !== (b2.mode & 1) && (null === a || 0 !== (L$1.current & 1) ? 0 === T$1 && (T$1 = 3) : tj()));
      null !== b2.updateQueue && (b2.flags |= 4);
      S(b2);
      return null;
    case 4:
      return zh(), Aj(a, b2), null === a && sf(b2.stateNode.containerInfo), S(b2), null;
    case 10:
      return ah(b2.type._context), S(b2), null;
    case 17:
      return Zf(b2.type) && $f(), S(b2), null;
    case 19:
      E$1(L$1);
      f2 = b2.memoizedState;
      if (null === f2) return S(b2), null;
      d2 = 0 !== (b2.flags & 128);
      g2 = f2.rendering;
      if (null === g2) if (d2) Dj(f2, false);
      else {
        if (0 !== T$1 || null !== a && 0 !== (a.flags & 128)) for (a = b2.child; null !== a; ) {
          g2 = Ch(a);
          if (null !== g2) {
            b2.flags |= 128;
            Dj(f2, false);
            d2 = g2.updateQueue;
            null !== d2 && (b2.updateQueue = d2, b2.flags |= 4);
            b2.subtreeFlags = 0;
            d2 = c;
            for (c = b2.child; null !== c; ) f2 = c, a = d2, f2.flags &= 14680066, g2 = f2.alternate, null === g2 ? (f2.childLanes = 0, f2.lanes = a, f2.child = null, f2.subtreeFlags = 0, f2.memoizedProps = null, f2.memoizedState = null, f2.updateQueue = null, f2.dependencies = null, f2.stateNode = null) : (f2.childLanes = g2.childLanes, f2.lanes = g2.lanes, f2.child = g2.child, f2.subtreeFlags = 0, f2.deletions = null, f2.memoizedProps = g2.memoizedProps, f2.memoizedState = g2.memoizedState, f2.updateQueue = g2.updateQueue, f2.type = g2.type, a = g2.dependencies, f2.dependencies = null === a ? null : { lanes: a.lanes, firstContext: a.firstContext }), c = c.sibling;
            G(L$1, L$1.current & 1 | 2);
            return b2.child;
          }
          a = a.sibling;
        }
        null !== f2.tail && B$1() > Gj && (b2.flags |= 128, d2 = true, Dj(f2, false), b2.lanes = 4194304);
      }
      else {
        if (!d2) if (a = Ch(g2), null !== a) {
          if (b2.flags |= 128, d2 = true, c = a.updateQueue, null !== c && (b2.updateQueue = c, b2.flags |= 4), Dj(f2, true), null === f2.tail && "hidden" === f2.tailMode && !g2.alternate && !I$1) return S(b2), null;
        } else 2 * B$1() - f2.renderingStartTime > Gj && 1073741824 !== c && (b2.flags |= 128, d2 = true, Dj(f2, false), b2.lanes = 4194304);
        f2.isBackwards ? (g2.sibling = b2.child, b2.child = g2) : (c = f2.last, null !== c ? c.sibling = g2 : b2.child = g2, f2.last = g2);
      }
      if (null !== f2.tail) return b2 = f2.tail, f2.rendering = b2, f2.tail = b2.sibling, f2.renderingStartTime = B$1(), b2.sibling = null, c = L$1.current, G(L$1, d2 ? c & 1 | 2 : c & 1), b2;
      S(b2);
      return null;
    case 22:
    case 23:
      return Hj(), d2 = null !== b2.memoizedState, null !== a && null !== a.memoizedState !== d2 && (b2.flags |= 8192), d2 && 0 !== (b2.mode & 1) ? 0 !== (fj & 1073741824) && (S(b2), b2.subtreeFlags & 6 && (b2.flags |= 8192)) : S(b2), null;
    case 24:
      return null;
    case 25:
      return null;
  }
  throw Error(p(156, b2.tag));
}
function Ij(a, b2) {
  wg(b2);
  switch (b2.tag) {
    case 1:
      return Zf(b2.type) && $f(), a = b2.flags, a & 65536 ? (b2.flags = a & -65537 | 128, b2) : null;
    case 3:
      return zh(), E$1(Wf), E$1(H$1), Eh(), a = b2.flags, 0 !== (a & 65536) && 0 === (a & 128) ? (b2.flags = a & -65537 | 128, b2) : null;
    case 5:
      return Bh(b2), null;
    case 13:
      E$1(L$1);
      a = b2.memoizedState;
      if (null !== a && null !== a.dehydrated) {
        if (null === b2.alternate) throw Error(p(340));
        Ig();
      }
      a = b2.flags;
      return a & 65536 ? (b2.flags = a & -65537 | 128, b2) : null;
    case 19:
      return E$1(L$1), null;
    case 4:
      return zh(), null;
    case 10:
      return ah(b2.type._context), null;
    case 22:
    case 23:
      return Hj(), null;
    case 24:
      return null;
    default:
      return null;
  }
}
var Jj = false, U$1 = false, Kj = "function" === typeof WeakSet ? WeakSet : Set, V$1 = null;
function Lj(a, b2) {
  var c = a.ref;
  if (null !== c) if ("function" === typeof c) try {
    c(null);
  } catch (d2) {
    W$1(a, b2, d2);
  }
  else c.current = null;
}
function Mj(a, b2, c) {
  try {
    c();
  } catch (d2) {
    W$1(a, b2, d2);
  }
}
var Nj = false;
function Oj(a, b2) {
  Cf = dd;
  a = Me$1();
  if (Ne$1(a)) {
    if ("selectionStart" in a) var c = { start: a.selectionStart, end: a.selectionEnd };
    else a: {
      c = (c = a.ownerDocument) && c.defaultView || window;
      var d2 = c.getSelection && c.getSelection();
      if (d2 && 0 !== d2.rangeCount) {
        c = d2.anchorNode;
        var e = d2.anchorOffset, f2 = d2.focusNode;
        d2 = d2.focusOffset;
        try {
          c.nodeType, f2.nodeType;
        } catch (F2) {
          c = null;
          break a;
        }
        var g2 = 0, h = -1, k2 = -1, l4 = 0, m2 = 0, q2 = a, r2 = null;
        b: for (; ; ) {
          for (var y2; ; ) {
            q2 !== c || 0 !== e && 3 !== q2.nodeType || (h = g2 + e);
            q2 !== f2 || 0 !== d2 && 3 !== q2.nodeType || (k2 = g2 + d2);
            3 === q2.nodeType && (g2 += q2.nodeValue.length);
            if (null === (y2 = q2.firstChild)) break;
            r2 = q2;
            q2 = y2;
          }
          for (; ; ) {
            if (q2 === a) break b;
            r2 === c && ++l4 === e && (h = g2);
            r2 === f2 && ++m2 === d2 && (k2 = g2);
            if (null !== (y2 = q2.nextSibling)) break;
            q2 = r2;
            r2 = q2.parentNode;
          }
          q2 = y2;
        }
        c = -1 === h || -1 === k2 ? null : { start: h, end: k2 };
      } else c = null;
    }
    c = c || { start: 0, end: 0 };
  } else c = null;
  Df = { focusedElem: a, selectionRange: c };
  dd = false;
  for (V$1 = b2; null !== V$1; ) if (b2 = V$1, a = b2.child, 0 !== (b2.subtreeFlags & 1028) && null !== a) a.return = b2, V$1 = a;
  else for (; null !== V$1; ) {
    b2 = V$1;
    try {
      var n2 = b2.alternate;
      if (0 !== (b2.flags & 1024)) switch (b2.tag) {
        case 0:
        case 11:
        case 15:
          break;
        case 1:
          if (null !== n2) {
            var t2 = n2.memoizedProps, J2 = n2.memoizedState, x2 = b2.stateNode, w2 = x2.getSnapshotBeforeUpdate(b2.elementType === b2.type ? t2 : Ci(b2.type, t2), J2);
            x2.__reactInternalSnapshotBeforeUpdate = w2;
          }
          break;
        case 3:
          var u2 = b2.stateNode.containerInfo;
          1 === u2.nodeType ? u2.textContent = "" : 9 === u2.nodeType && u2.documentElement && u2.removeChild(u2.documentElement);
          break;
        case 5:
        case 6:
        case 4:
        case 17:
          break;
        default:
          throw Error(p(163));
      }
    } catch (F2) {
      W$1(b2, b2.return, F2);
    }
    a = b2.sibling;
    if (null !== a) {
      a.return = b2.return;
      V$1 = a;
      break;
    }
    V$1 = b2.return;
  }
  n2 = Nj;
  Nj = false;
  return n2;
}
function Pj(a, b2, c) {
  var d2 = b2.updateQueue;
  d2 = null !== d2 ? d2.lastEffect : null;
  if (null !== d2) {
    var e = d2 = d2.next;
    do {
      if ((e.tag & a) === a) {
        var f2 = e.destroy;
        e.destroy = void 0;
        void 0 !== f2 && Mj(b2, c, f2);
      }
      e = e.next;
    } while (e !== d2);
  }
}
function Qj(a, b2) {
  b2 = b2.updateQueue;
  b2 = null !== b2 ? b2.lastEffect : null;
  if (null !== b2) {
    var c = b2 = b2.next;
    do {
      if ((c.tag & a) === a) {
        var d2 = c.create;
        c.destroy = d2();
      }
      c = c.next;
    } while (c !== b2);
  }
}
function Rj(a) {
  var b2 = a.ref;
  if (null !== b2) {
    var c = a.stateNode;
    switch (a.tag) {
      case 5:
        a = c;
        break;
      default:
        a = c;
    }
    "function" === typeof b2 ? b2(a) : b2.current = a;
  }
}
function Sj(a) {
  var b2 = a.alternate;
  null !== b2 && (a.alternate = null, Sj(b2));
  a.child = null;
  a.deletions = null;
  a.sibling = null;
  5 === a.tag && (b2 = a.stateNode, null !== b2 && (delete b2[Of], delete b2[Pf], delete b2[of], delete b2[Qf], delete b2[Rf]));
  a.stateNode = null;
  a.return = null;
  a.dependencies = null;
  a.memoizedProps = null;
  a.memoizedState = null;
  a.pendingProps = null;
  a.stateNode = null;
  a.updateQueue = null;
}
function Tj(a) {
  return 5 === a.tag || 3 === a.tag || 4 === a.tag;
}
function Uj(a) {
  a: for (; ; ) {
    for (; null === a.sibling; ) {
      if (null === a.return || Tj(a.return)) return null;
      a = a.return;
    }
    a.sibling.return = a.return;
    for (a = a.sibling; 5 !== a.tag && 6 !== a.tag && 18 !== a.tag; ) {
      if (a.flags & 2) continue a;
      if (null === a.child || 4 === a.tag) continue a;
      else a.child.return = a, a = a.child;
    }
    if (!(a.flags & 2)) return a.stateNode;
  }
}
function Vj(a, b2, c) {
  var d2 = a.tag;
  if (5 === d2 || 6 === d2) a = a.stateNode, b2 ? 8 === c.nodeType ? c.parentNode.insertBefore(a, b2) : c.insertBefore(a, b2) : (8 === c.nodeType ? (b2 = c.parentNode, b2.insertBefore(a, c)) : (b2 = c, b2.appendChild(a)), c = c._reactRootContainer, null !== c && void 0 !== c || null !== b2.onclick || (b2.onclick = Bf));
  else if (4 !== d2 && (a = a.child, null !== a)) for (Vj(a, b2, c), a = a.sibling; null !== a; ) Vj(a, b2, c), a = a.sibling;
}
function Wj(a, b2, c) {
  var d2 = a.tag;
  if (5 === d2 || 6 === d2) a = a.stateNode, b2 ? c.insertBefore(a, b2) : c.appendChild(a);
  else if (4 !== d2 && (a = a.child, null !== a)) for (Wj(a, b2, c), a = a.sibling; null !== a; ) Wj(a, b2, c), a = a.sibling;
}
var X$1 = null, Xj = false;
function Yj(a, b2, c) {
  for (c = c.child; null !== c; ) Zj(a, b2, c), c = c.sibling;
}
function Zj(a, b2, c) {
  if (lc && "function" === typeof lc.onCommitFiberUnmount) try {
    lc.onCommitFiberUnmount(kc, c);
  } catch (h) {
  }
  switch (c.tag) {
    case 5:
      U$1 || Lj(c, b2);
    case 6:
      var d2 = X$1, e = Xj;
      X$1 = null;
      Yj(a, b2, c);
      X$1 = d2;
      Xj = e;
      null !== X$1 && (Xj ? (a = X$1, c = c.stateNode, 8 === a.nodeType ? a.parentNode.removeChild(c) : a.removeChild(c)) : X$1.removeChild(c.stateNode));
      break;
    case 18:
      null !== X$1 && (Xj ? (a = X$1, c = c.stateNode, 8 === a.nodeType ? Kf(a.parentNode, c) : 1 === a.nodeType && Kf(a, c), bd(a)) : Kf(X$1, c.stateNode));
      break;
    case 4:
      d2 = X$1;
      e = Xj;
      X$1 = c.stateNode.containerInfo;
      Xj = true;
      Yj(a, b2, c);
      X$1 = d2;
      Xj = e;
      break;
    case 0:
    case 11:
    case 14:
    case 15:
      if (!U$1 && (d2 = c.updateQueue, null !== d2 && (d2 = d2.lastEffect, null !== d2))) {
        e = d2 = d2.next;
        do {
          var f2 = e, g2 = f2.destroy;
          f2 = f2.tag;
          void 0 !== g2 && (0 !== (f2 & 2) ? Mj(c, b2, g2) : 0 !== (f2 & 4) && Mj(c, b2, g2));
          e = e.next;
        } while (e !== d2);
      }
      Yj(a, b2, c);
      break;
    case 1:
      if (!U$1 && (Lj(c, b2), d2 = c.stateNode, "function" === typeof d2.componentWillUnmount)) try {
        d2.props = c.memoizedProps, d2.state = c.memoizedState, d2.componentWillUnmount();
      } catch (h) {
        W$1(c, b2, h);
      }
      Yj(a, b2, c);
      break;
    case 21:
      Yj(a, b2, c);
      break;
    case 22:
      c.mode & 1 ? (U$1 = (d2 = U$1) || null !== c.memoizedState, Yj(a, b2, c), U$1 = d2) : Yj(a, b2, c);
      break;
    default:
      Yj(a, b2, c);
  }
}
function ak(a) {
  var b2 = a.updateQueue;
  if (null !== b2) {
    a.updateQueue = null;
    var c = a.stateNode;
    null === c && (c = a.stateNode = new Kj());
    b2.forEach(function(b3) {
      var d2 = bk.bind(null, a, b3);
      c.has(b3) || (c.add(b3), b3.then(d2, d2));
    });
  }
}
function ck(a, b2) {
  var c = b2.deletions;
  if (null !== c) for (var d2 = 0; d2 < c.length; d2++) {
    var e = c[d2];
    try {
      var f2 = a, g2 = b2, h = g2;
      a: for (; null !== h; ) {
        switch (h.tag) {
          case 5:
            X$1 = h.stateNode;
            Xj = false;
            break a;
          case 3:
            X$1 = h.stateNode.containerInfo;
            Xj = true;
            break a;
          case 4:
            X$1 = h.stateNode.containerInfo;
            Xj = true;
            break a;
        }
        h = h.return;
      }
      if (null === X$1) throw Error(p(160));
      Zj(f2, g2, e);
      X$1 = null;
      Xj = false;
      var k2 = e.alternate;
      null !== k2 && (k2.return = null);
      e.return = null;
    } catch (l4) {
      W$1(e, b2, l4);
    }
  }
  if (b2.subtreeFlags & 12854) for (b2 = b2.child; null !== b2; ) dk(b2, a), b2 = b2.sibling;
}
function dk(a, b2) {
  var c = a.alternate, d2 = a.flags;
  switch (a.tag) {
    case 0:
    case 11:
    case 14:
    case 15:
      ck(b2, a);
      ek(a);
      if (d2 & 4) {
        try {
          Pj(3, a, a.return), Qj(3, a);
        } catch (t2) {
          W$1(a, a.return, t2);
        }
        try {
          Pj(5, a, a.return);
        } catch (t2) {
          W$1(a, a.return, t2);
        }
      }
      break;
    case 1:
      ck(b2, a);
      ek(a);
      d2 & 512 && null !== c && Lj(c, c.return);
      break;
    case 5:
      ck(b2, a);
      ek(a);
      d2 & 512 && null !== c && Lj(c, c.return);
      if (a.flags & 32) {
        var e = a.stateNode;
        try {
          ob(e, "");
        } catch (t2) {
          W$1(a, a.return, t2);
        }
      }
      if (d2 & 4 && (e = a.stateNode, null != e)) {
        var f2 = a.memoizedProps, g2 = null !== c ? c.memoizedProps : f2, h = a.type, k2 = a.updateQueue;
        a.updateQueue = null;
        if (null !== k2) try {
          "input" === h && "radio" === f2.type && null != f2.name && ab(e, f2);
          vb(h, g2);
          var l4 = vb(h, f2);
          for (g2 = 0; g2 < k2.length; g2 += 2) {
            var m2 = k2[g2], q2 = k2[g2 + 1];
            "style" === m2 ? sb(e, q2) : "dangerouslySetInnerHTML" === m2 ? nb(e, q2) : "children" === m2 ? ob(e, q2) : ta(e, m2, q2, l4);
          }
          switch (h) {
            case "input":
              bb(e, f2);
              break;
            case "textarea":
              ib(e, f2);
              break;
            case "select":
              var r2 = e._wrapperState.wasMultiple;
              e._wrapperState.wasMultiple = !!f2.multiple;
              var y2 = f2.value;
              null != y2 ? fb(e, !!f2.multiple, y2, false) : r2 !== !!f2.multiple && (null != f2.defaultValue ? fb(
                e,
                !!f2.multiple,
                f2.defaultValue,
                true
              ) : fb(e, !!f2.multiple, f2.multiple ? [] : "", false));
          }
          e[Pf] = f2;
        } catch (t2) {
          W$1(a, a.return, t2);
        }
      }
      break;
    case 6:
      ck(b2, a);
      ek(a);
      if (d2 & 4) {
        if (null === a.stateNode) throw Error(p(162));
        e = a.stateNode;
        f2 = a.memoizedProps;
        try {
          e.nodeValue = f2;
        } catch (t2) {
          W$1(a, a.return, t2);
        }
      }
      break;
    case 3:
      ck(b2, a);
      ek(a);
      if (d2 & 4 && null !== c && c.memoizedState.isDehydrated) try {
        bd(b2.containerInfo);
      } catch (t2) {
        W$1(a, a.return, t2);
      }
      break;
    case 4:
      ck(b2, a);
      ek(a);
      break;
    case 13:
      ck(b2, a);
      ek(a);
      e = a.child;
      e.flags & 8192 && (f2 = null !== e.memoizedState, e.stateNode.isHidden = f2, !f2 || null !== e.alternate && null !== e.alternate.memoizedState || (fk = B$1()));
      d2 & 4 && ak(a);
      break;
    case 22:
      m2 = null !== c && null !== c.memoizedState;
      a.mode & 1 ? (U$1 = (l4 = U$1) || m2, ck(b2, a), U$1 = l4) : ck(b2, a);
      ek(a);
      if (d2 & 8192) {
        l4 = null !== a.memoizedState;
        if ((a.stateNode.isHidden = l4) && !m2 && 0 !== (a.mode & 1)) for (V$1 = a, m2 = a.child; null !== m2; ) {
          for (q2 = V$1 = m2; null !== V$1; ) {
            r2 = V$1;
            y2 = r2.child;
            switch (r2.tag) {
              case 0:
              case 11:
              case 14:
              case 15:
                Pj(4, r2, r2.return);
                break;
              case 1:
                Lj(r2, r2.return);
                var n2 = r2.stateNode;
                if ("function" === typeof n2.componentWillUnmount) {
                  d2 = r2;
                  c = r2.return;
                  try {
                    b2 = d2, n2.props = b2.memoizedProps, n2.state = b2.memoizedState, n2.componentWillUnmount();
                  } catch (t2) {
                    W$1(d2, c, t2);
                  }
                }
                break;
              case 5:
                Lj(r2, r2.return);
                break;
              case 22:
                if (null !== r2.memoizedState) {
                  gk(q2);
                  continue;
                }
            }
            null !== y2 ? (y2.return = r2, V$1 = y2) : gk(q2);
          }
          m2 = m2.sibling;
        }
        a: for (m2 = null, q2 = a; ; ) {
          if (5 === q2.tag) {
            if (null === m2) {
              m2 = q2;
              try {
                e = q2.stateNode, l4 ? (f2 = e.style, "function" === typeof f2.setProperty ? f2.setProperty("display", "none", "important") : f2.display = "none") : (h = q2.stateNode, k2 = q2.memoizedProps.style, g2 = void 0 !== k2 && null !== k2 && k2.hasOwnProperty("display") ? k2.display : null, h.style.display = rb("display", g2));
              } catch (t2) {
                W$1(a, a.return, t2);
              }
            }
          } else if (6 === q2.tag) {
            if (null === m2) try {
              q2.stateNode.nodeValue = l4 ? "" : q2.memoizedProps;
            } catch (t2) {
              W$1(a, a.return, t2);
            }
          } else if ((22 !== q2.tag && 23 !== q2.tag || null === q2.memoizedState || q2 === a) && null !== q2.child) {
            q2.child.return = q2;
            q2 = q2.child;
            continue;
          }
          if (q2 === a) break a;
          for (; null === q2.sibling; ) {
            if (null === q2.return || q2.return === a) break a;
            m2 === q2 && (m2 = null);
            q2 = q2.return;
          }
          m2 === q2 && (m2 = null);
          q2.sibling.return = q2.return;
          q2 = q2.sibling;
        }
      }
      break;
    case 19:
      ck(b2, a);
      ek(a);
      d2 & 4 && ak(a);
      break;
    case 21:
      break;
    default:
      ck(
        b2,
        a
      ), ek(a);
  }
}
function ek(a) {
  var b2 = a.flags;
  if (b2 & 2) {
    try {
      a: {
        for (var c = a.return; null !== c; ) {
          if (Tj(c)) {
            var d2 = c;
            break a;
          }
          c = c.return;
        }
        throw Error(p(160));
      }
      switch (d2.tag) {
        case 5:
          var e = d2.stateNode;
          d2.flags & 32 && (ob(e, ""), d2.flags &= -33);
          var f2 = Uj(a);
          Wj(a, f2, e);
          break;
        case 3:
        case 4:
          var g2 = d2.stateNode.containerInfo, h = Uj(a);
          Vj(a, h, g2);
          break;
        default:
          throw Error(p(161));
      }
    } catch (k2) {
      W$1(a, a.return, k2);
    }
    a.flags &= -3;
  }
  b2 & 4096 && (a.flags &= -4097);
}
function hk(a, b2, c) {
  V$1 = a;
  ik(a);
}
function ik(a, b2, c) {
  for (var d2 = 0 !== (a.mode & 1); null !== V$1; ) {
    var e = V$1, f2 = e.child;
    if (22 === e.tag && d2) {
      var g2 = null !== e.memoizedState || Jj;
      if (!g2) {
        var h = e.alternate, k2 = null !== h && null !== h.memoizedState || U$1;
        h = Jj;
        var l4 = U$1;
        Jj = g2;
        if ((U$1 = k2) && !l4) for (V$1 = e; null !== V$1; ) g2 = V$1, k2 = g2.child, 22 === g2.tag && null !== g2.memoizedState ? jk(e) : null !== k2 ? (k2.return = g2, V$1 = k2) : jk(e);
        for (; null !== f2; ) V$1 = f2, ik(f2), f2 = f2.sibling;
        V$1 = e;
        Jj = h;
        U$1 = l4;
      }
      kk(a);
    } else 0 !== (e.subtreeFlags & 8772) && null !== f2 ? (f2.return = e, V$1 = f2) : kk(a);
  }
}
function kk(a) {
  for (; null !== V$1; ) {
    var b2 = V$1;
    if (0 !== (b2.flags & 8772)) {
      var c = b2.alternate;
      try {
        if (0 !== (b2.flags & 8772)) switch (b2.tag) {
          case 0:
          case 11:
          case 15:
            U$1 || Qj(5, b2);
            break;
          case 1:
            var d2 = b2.stateNode;
            if (b2.flags & 4 && !U$1) if (null === c) d2.componentDidMount();
            else {
              var e = b2.elementType === b2.type ? c.memoizedProps : Ci(b2.type, c.memoizedProps);
              d2.componentDidUpdate(e, c.memoizedState, d2.__reactInternalSnapshotBeforeUpdate);
            }
            var f2 = b2.updateQueue;
            null !== f2 && sh(b2, f2, d2);
            break;
          case 3:
            var g2 = b2.updateQueue;
            if (null !== g2) {
              c = null;
              if (null !== b2.child) switch (b2.child.tag) {
                case 5:
                  c = b2.child.stateNode;
                  break;
                case 1:
                  c = b2.child.stateNode;
              }
              sh(b2, g2, c);
            }
            break;
          case 5:
            var h = b2.stateNode;
            if (null === c && b2.flags & 4) {
              c = h;
              var k2 = b2.memoizedProps;
              switch (b2.type) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  k2.autoFocus && c.focus();
                  break;
                case "img":
                  k2.src && (c.src = k2.src);
              }
            }
            break;
          case 6:
            break;
          case 4:
            break;
          case 12:
            break;
          case 13:
            if (null === b2.memoizedState) {
              var l4 = b2.alternate;
              if (null !== l4) {
                var m2 = l4.memoizedState;
                if (null !== m2) {
                  var q2 = m2.dehydrated;
                  null !== q2 && bd(q2);
                }
              }
            }
            break;
          case 19:
          case 17:
          case 21:
          case 22:
          case 23:
          case 25:
            break;
          default:
            throw Error(p(163));
        }
        U$1 || b2.flags & 512 && Rj(b2);
      } catch (r2) {
        W$1(b2, b2.return, r2);
      }
    }
    if (b2 === a) {
      V$1 = null;
      break;
    }
    c = b2.sibling;
    if (null !== c) {
      c.return = b2.return;
      V$1 = c;
      break;
    }
    V$1 = b2.return;
  }
}
function gk(a) {
  for (; null !== V$1; ) {
    var b2 = V$1;
    if (b2 === a) {
      V$1 = null;
      break;
    }
    var c = b2.sibling;
    if (null !== c) {
      c.return = b2.return;
      V$1 = c;
      break;
    }
    V$1 = b2.return;
  }
}
function jk(a) {
  for (; null !== V$1; ) {
    var b2 = V$1;
    try {
      switch (b2.tag) {
        case 0:
        case 11:
        case 15:
          var c = b2.return;
          try {
            Qj(4, b2);
          } catch (k2) {
            W$1(b2, c, k2);
          }
          break;
        case 1:
          var d2 = b2.stateNode;
          if ("function" === typeof d2.componentDidMount) {
            var e = b2.return;
            try {
              d2.componentDidMount();
            } catch (k2) {
              W$1(b2, e, k2);
            }
          }
          var f2 = b2.return;
          try {
            Rj(b2);
          } catch (k2) {
            W$1(b2, f2, k2);
          }
          break;
        case 5:
          var g2 = b2.return;
          try {
            Rj(b2);
          } catch (k2) {
            W$1(b2, g2, k2);
          }
      }
    } catch (k2) {
      W$1(b2, b2.return, k2);
    }
    if (b2 === a) {
      V$1 = null;
      break;
    }
    var h = b2.sibling;
    if (null !== h) {
      h.return = b2.return;
      V$1 = h;
      break;
    }
    V$1 = b2.return;
  }
}
var lk = Math.ceil, mk = ua.ReactCurrentDispatcher, nk = ua.ReactCurrentOwner, ok = ua.ReactCurrentBatchConfig, K$1 = 0, Q$1 = null, Y$1 = null, Z$1 = 0, fj = 0, ej = Uf(0), T$1 = 0, pk = null, rh = 0, qk = 0, rk = 0, sk = null, tk = null, fk = 0, Gj = Infinity, uk = null, Oi = false, Pi = null, Ri = null, vk = false, wk = null, xk = 0, yk = 0, zk = null, Ak = -1, Bk = 0;
function R() {
  return 0 !== (K$1 & 6) ? B$1() : -1 !== Ak ? Ak : Ak = B$1();
}
function yi(a) {
  if (0 === (a.mode & 1)) return 1;
  if (0 !== (K$1 & 2) && 0 !== Z$1) return Z$1 & -Z$1;
  if (null !== Kg.transition) return 0 === Bk && (Bk = yc()), Bk;
  a = C;
  if (0 !== a) return a;
  a = window.event;
  a = void 0 === a ? 16 : jd(a.type);
  return a;
}
function gi(a, b2, c, d2) {
  if (50 < yk) throw yk = 0, zk = null, Error(p(185));
  Ac(a, c, d2);
  if (0 === (K$1 & 2) || a !== Q$1) a === Q$1 && (0 === (K$1 & 2) && (qk |= c), 4 === T$1 && Ck(a, Z$1)), Dk(a, d2), 1 === c && 0 === K$1 && 0 === (b2.mode & 1) && (Gj = B$1() + 500, fg && jg());
}
function Dk(a, b2) {
  var c = a.callbackNode;
  wc(a, b2);
  var d2 = uc(a, a === Q$1 ? Z$1 : 0);
  if (0 === d2) null !== c && bc(c), a.callbackNode = null, a.callbackPriority = 0;
  else if (b2 = d2 & -d2, a.callbackPriority !== b2) {
    null != c && bc(c);
    if (1 === b2) 0 === a.tag ? ig(Ek.bind(null, a)) : hg(Ek.bind(null, a)), Jf(function() {
      0 === (K$1 & 6) && jg();
    }), c = null;
    else {
      switch (Dc(d2)) {
        case 1:
          c = fc;
          break;
        case 4:
          c = gc;
          break;
        case 16:
          c = hc;
          break;
        case 536870912:
          c = jc;
          break;
        default:
          c = hc;
      }
      c = Fk(c, Gk.bind(null, a));
    }
    a.callbackPriority = b2;
    a.callbackNode = c;
  }
}
function Gk(a, b2) {
  Ak = -1;
  Bk = 0;
  if (0 !== (K$1 & 6)) throw Error(p(327));
  var c = a.callbackNode;
  if (Hk() && a.callbackNode !== c) return null;
  var d2 = uc(a, a === Q$1 ? Z$1 : 0);
  if (0 === d2) return null;
  if (0 !== (d2 & 30) || 0 !== (d2 & a.expiredLanes) || b2) b2 = Ik(a, d2);
  else {
    b2 = d2;
    var e = K$1;
    K$1 |= 2;
    var f2 = Jk();
    if (Q$1 !== a || Z$1 !== b2) uk = null, Gj = B$1() + 500, Kk(a, b2);
    do
      try {
        Lk();
        break;
      } catch (h) {
        Mk(a, h);
      }
    while (1);
    $g();
    mk.current = f2;
    K$1 = e;
    null !== Y$1 ? b2 = 0 : (Q$1 = null, Z$1 = 0, b2 = T$1);
  }
  if (0 !== b2) {
    2 === b2 && (e = xc(a), 0 !== e && (d2 = e, b2 = Nk(a, e)));
    if (1 === b2) throw c = pk, Kk(a, 0), Ck(a, d2), Dk(a, B$1()), c;
    if (6 === b2) Ck(a, d2);
    else {
      e = a.current.alternate;
      if (0 === (d2 & 30) && !Ok(e) && (b2 = Ik(a, d2), 2 === b2 && (f2 = xc(a), 0 !== f2 && (d2 = f2, b2 = Nk(a, f2))), 1 === b2)) throw c = pk, Kk(a, 0), Ck(a, d2), Dk(a, B$1()), c;
      a.finishedWork = e;
      a.finishedLanes = d2;
      switch (b2) {
        case 0:
        case 1:
          throw Error(p(345));
        case 2:
          Pk(a, tk, uk);
          break;
        case 3:
          Ck(a, d2);
          if ((d2 & 130023424) === d2 && (b2 = fk + 500 - B$1(), 10 < b2)) {
            if (0 !== uc(a, 0)) break;
            e = a.suspendedLanes;
            if ((e & d2) !== d2) {
              R();
              a.pingedLanes |= a.suspendedLanes & e;
              break;
            }
            a.timeoutHandle = Ff(Pk.bind(null, a, tk, uk), b2);
            break;
          }
          Pk(a, tk, uk);
          break;
        case 4:
          Ck(a, d2);
          if ((d2 & 4194240) === d2) break;
          b2 = a.eventTimes;
          for (e = -1; 0 < d2; ) {
            var g2 = 31 - oc(d2);
            f2 = 1 << g2;
            g2 = b2[g2];
            g2 > e && (e = g2);
            d2 &= ~f2;
          }
          d2 = e;
          d2 = B$1() - d2;
          d2 = (120 > d2 ? 120 : 480 > d2 ? 480 : 1080 > d2 ? 1080 : 1920 > d2 ? 1920 : 3e3 > d2 ? 3e3 : 4320 > d2 ? 4320 : 1960 * lk(d2 / 1960)) - d2;
          if (10 < d2) {
            a.timeoutHandle = Ff(Pk.bind(null, a, tk, uk), d2);
            break;
          }
          Pk(a, tk, uk);
          break;
        case 5:
          Pk(a, tk, uk);
          break;
        default:
          throw Error(p(329));
      }
    }
  }
  Dk(a, B$1());
  return a.callbackNode === c ? Gk.bind(null, a) : null;
}
function Nk(a, b2) {
  var c = sk;
  a.current.memoizedState.isDehydrated && (Kk(a, b2).flags |= 256);
  a = Ik(a, b2);
  2 !== a && (b2 = tk, tk = c, null !== b2 && Fj(b2));
  return a;
}
function Fj(a) {
  null === tk ? tk = a : tk.push.apply(tk, a);
}
function Ok(a) {
  for (var b2 = a; ; ) {
    if (b2.flags & 16384) {
      var c = b2.updateQueue;
      if (null !== c && (c = c.stores, null !== c)) for (var d2 = 0; d2 < c.length; d2++) {
        var e = c[d2], f2 = e.getSnapshot;
        e = e.value;
        try {
          if (!He$1(f2(), e)) return false;
        } catch (g2) {
          return false;
        }
      }
    }
    c = b2.child;
    if (b2.subtreeFlags & 16384 && null !== c) c.return = b2, b2 = c;
    else {
      if (b2 === a) break;
      for (; null === b2.sibling; ) {
        if (null === b2.return || b2.return === a) return true;
        b2 = b2.return;
      }
      b2.sibling.return = b2.return;
      b2 = b2.sibling;
    }
  }
  return true;
}
function Ck(a, b2) {
  b2 &= ~rk;
  b2 &= ~qk;
  a.suspendedLanes |= b2;
  a.pingedLanes &= ~b2;
  for (a = a.expirationTimes; 0 < b2; ) {
    var c = 31 - oc(b2), d2 = 1 << c;
    a[c] = -1;
    b2 &= ~d2;
  }
}
function Ek(a) {
  if (0 !== (K$1 & 6)) throw Error(p(327));
  Hk();
  var b2 = uc(a, 0);
  if (0 === (b2 & 1)) return Dk(a, B$1()), null;
  var c = Ik(a, b2);
  if (0 !== a.tag && 2 === c) {
    var d2 = xc(a);
    0 !== d2 && (b2 = d2, c = Nk(a, d2));
  }
  if (1 === c) throw c = pk, Kk(a, 0), Ck(a, b2), Dk(a, B$1()), c;
  if (6 === c) throw Error(p(345));
  a.finishedWork = a.current.alternate;
  a.finishedLanes = b2;
  Pk(a, tk, uk);
  Dk(a, B$1());
  return null;
}
function Qk(a, b2) {
  var c = K$1;
  K$1 |= 1;
  try {
    return a(b2);
  } finally {
    K$1 = c, 0 === K$1 && (Gj = B$1() + 500, fg && jg());
  }
}
function Rk(a) {
  null !== wk && 0 === wk.tag && 0 === (K$1 & 6) && Hk();
  var b2 = K$1;
  K$1 |= 1;
  var c = ok.transition, d2 = C;
  try {
    if (ok.transition = null, C = 1, a) return a();
  } finally {
    C = d2, ok.transition = c, K$1 = b2, 0 === (K$1 & 6) && jg();
  }
}
function Hj() {
  fj = ej.current;
  E$1(ej);
}
function Kk(a, b2) {
  a.finishedWork = null;
  a.finishedLanes = 0;
  var c = a.timeoutHandle;
  -1 !== c && (a.timeoutHandle = -1, Gf(c));
  if (null !== Y$1) for (c = Y$1.return; null !== c; ) {
    var d2 = c;
    wg(d2);
    switch (d2.tag) {
      case 1:
        d2 = d2.type.childContextTypes;
        null !== d2 && void 0 !== d2 && $f();
        break;
      case 3:
        zh();
        E$1(Wf);
        E$1(H$1);
        Eh();
        break;
      case 5:
        Bh(d2);
        break;
      case 4:
        zh();
        break;
      case 13:
        E$1(L$1);
        break;
      case 19:
        E$1(L$1);
        break;
      case 10:
        ah(d2.type._context);
        break;
      case 22:
      case 23:
        Hj();
    }
    c = c.return;
  }
  Q$1 = a;
  Y$1 = a = Pg(a.current, null);
  Z$1 = fj = b2;
  T$1 = 0;
  pk = null;
  rk = qk = rh = 0;
  tk = sk = null;
  if (null !== fh) {
    for (b2 = 0; b2 < fh.length; b2++) if (c = fh[b2], d2 = c.interleaved, null !== d2) {
      c.interleaved = null;
      var e = d2.next, f2 = c.pending;
      if (null !== f2) {
        var g2 = f2.next;
        f2.next = e;
        d2.next = g2;
      }
      c.pending = d2;
    }
    fh = null;
  }
  return a;
}
function Mk(a, b2) {
  do {
    var c = Y$1;
    try {
      $g();
      Fh.current = Rh;
      if (Ih) {
        for (var d2 = M$1.memoizedState; null !== d2; ) {
          var e = d2.queue;
          null !== e && (e.pending = null);
          d2 = d2.next;
        }
        Ih = false;
      }
      Hh = 0;
      O$1 = N$1 = M$1 = null;
      Jh = false;
      Kh = 0;
      nk.current = null;
      if (null === c || null === c.return) {
        T$1 = 1;
        pk = b2;
        Y$1 = null;
        break;
      }
      a: {
        var f2 = a, g2 = c.return, h = c, k2 = b2;
        b2 = Z$1;
        h.flags |= 32768;
        if (null !== k2 && "object" === typeof k2 && "function" === typeof k2.then) {
          var l4 = k2, m2 = h, q2 = m2.tag;
          if (0 === (m2.mode & 1) && (0 === q2 || 11 === q2 || 15 === q2)) {
            var r2 = m2.alternate;
            r2 ? (m2.updateQueue = r2.updateQueue, m2.memoizedState = r2.memoizedState, m2.lanes = r2.lanes) : (m2.updateQueue = null, m2.memoizedState = null);
          }
          var y2 = Ui(g2);
          if (null !== y2) {
            y2.flags &= -257;
            Vi(y2, g2, h, f2, b2);
            y2.mode & 1 && Si(f2, l4, b2);
            b2 = y2;
            k2 = l4;
            var n2 = b2.updateQueue;
            if (null === n2) {
              var t2 = /* @__PURE__ */ new Set();
              t2.add(k2);
              b2.updateQueue = t2;
            } else n2.add(k2);
            break a;
          } else {
            if (0 === (b2 & 1)) {
              Si(f2, l4, b2);
              tj();
              break a;
            }
            k2 = Error(p(426));
          }
        } else if (I$1 && h.mode & 1) {
          var J2 = Ui(g2);
          if (null !== J2) {
            0 === (J2.flags & 65536) && (J2.flags |= 256);
            Vi(J2, g2, h, f2, b2);
            Jg(Ji(k2, h));
            break a;
          }
        }
        f2 = k2 = Ji(k2, h);
        4 !== T$1 && (T$1 = 2);
        null === sk ? sk = [f2] : sk.push(f2);
        f2 = g2;
        do {
          switch (f2.tag) {
            case 3:
              f2.flags |= 65536;
              b2 &= -b2;
              f2.lanes |= b2;
              var x2 = Ni(f2, k2, b2);
              ph(f2, x2);
              break a;
            case 1:
              h = k2;
              var w2 = f2.type, u2 = f2.stateNode;
              if (0 === (f2.flags & 128) && ("function" === typeof w2.getDerivedStateFromError || null !== u2 && "function" === typeof u2.componentDidCatch && (null === Ri || !Ri.has(u2)))) {
                f2.flags |= 65536;
                b2 &= -b2;
                f2.lanes |= b2;
                var F2 = Qi(f2, h, b2);
                ph(f2, F2);
                break a;
              }
          }
          f2 = f2.return;
        } while (null !== f2);
      }
      Sk(c);
    } catch (na) {
      b2 = na;
      Y$1 === c && null !== c && (Y$1 = c = c.return);
      continue;
    }
    break;
  } while (1);
}
function Jk() {
  var a = mk.current;
  mk.current = Rh;
  return null === a ? Rh : a;
}
function tj() {
  if (0 === T$1 || 3 === T$1 || 2 === T$1) T$1 = 4;
  null === Q$1 || 0 === (rh & 268435455) && 0 === (qk & 268435455) || Ck(Q$1, Z$1);
}
function Ik(a, b2) {
  var c = K$1;
  K$1 |= 2;
  var d2 = Jk();
  if (Q$1 !== a || Z$1 !== b2) uk = null, Kk(a, b2);
  do
    try {
      Tk();
      break;
    } catch (e) {
      Mk(a, e);
    }
  while (1);
  $g();
  K$1 = c;
  mk.current = d2;
  if (null !== Y$1) throw Error(p(261));
  Q$1 = null;
  Z$1 = 0;
  return T$1;
}
function Tk() {
  for (; null !== Y$1; ) Uk(Y$1);
}
function Lk() {
  for (; null !== Y$1 && !cc(); ) Uk(Y$1);
}
function Uk(a) {
  var b2 = Vk(a.alternate, a, fj);
  a.memoizedProps = a.pendingProps;
  null === b2 ? Sk(a) : Y$1 = b2;
  nk.current = null;
}
function Sk(a) {
  var b2 = a;
  do {
    var c = b2.alternate;
    a = b2.return;
    if (0 === (b2.flags & 32768)) {
      if (c = Ej(c, b2, fj), null !== c) {
        Y$1 = c;
        return;
      }
    } else {
      c = Ij(c, b2);
      if (null !== c) {
        c.flags &= 32767;
        Y$1 = c;
        return;
      }
      if (null !== a) a.flags |= 32768, a.subtreeFlags = 0, a.deletions = null;
      else {
        T$1 = 6;
        Y$1 = null;
        return;
      }
    }
    b2 = b2.sibling;
    if (null !== b2) {
      Y$1 = b2;
      return;
    }
    Y$1 = b2 = a;
  } while (null !== b2);
  0 === T$1 && (T$1 = 5);
}
function Pk(a, b2, c) {
  var d2 = C, e = ok.transition;
  try {
    ok.transition = null, C = 1, Wk(a, b2, c, d2);
  } finally {
    ok.transition = e, C = d2;
  }
  return null;
}
function Wk(a, b2, c, d2) {
  do
    Hk();
  while (null !== wk);
  if (0 !== (K$1 & 6)) throw Error(p(327));
  c = a.finishedWork;
  var e = a.finishedLanes;
  if (null === c) return null;
  a.finishedWork = null;
  a.finishedLanes = 0;
  if (c === a.current) throw Error(p(177));
  a.callbackNode = null;
  a.callbackPriority = 0;
  var f2 = c.lanes | c.childLanes;
  Bc(a, f2);
  a === Q$1 && (Y$1 = Q$1 = null, Z$1 = 0);
  0 === (c.subtreeFlags & 2064) && 0 === (c.flags & 2064) || vk || (vk = true, Fk(hc, function() {
    Hk();
    return null;
  }));
  f2 = 0 !== (c.flags & 15990);
  if (0 !== (c.subtreeFlags & 15990) || f2) {
    f2 = ok.transition;
    ok.transition = null;
    var g2 = C;
    C = 1;
    var h = K$1;
    K$1 |= 4;
    nk.current = null;
    Oj(a, c);
    dk(c, a);
    Oe$1(Df);
    dd = !!Cf;
    Df = Cf = null;
    a.current = c;
    hk(c);
    dc();
    K$1 = h;
    C = g2;
    ok.transition = f2;
  } else a.current = c;
  vk && (vk = false, wk = a, xk = e);
  f2 = a.pendingLanes;
  0 === f2 && (Ri = null);
  mc(c.stateNode);
  Dk(a, B$1());
  if (null !== b2) for (d2 = a.onRecoverableError, c = 0; c < b2.length; c++) e = b2[c], d2(e.value, { componentStack: e.stack, digest: e.digest });
  if (Oi) throw Oi = false, a = Pi, Pi = null, a;
  0 !== (xk & 1) && 0 !== a.tag && Hk();
  f2 = a.pendingLanes;
  0 !== (f2 & 1) ? a === zk ? yk++ : (yk = 0, zk = a) : yk = 0;
  jg();
  return null;
}
function Hk() {
  if (null !== wk) {
    var a = Dc(xk), b2 = ok.transition, c = C;
    try {
      ok.transition = null;
      C = 16 > a ? 16 : a;
      if (null === wk) var d2 = false;
      else {
        a = wk;
        wk = null;
        xk = 0;
        if (0 !== (K$1 & 6)) throw Error(p(331));
        var e = K$1;
        K$1 |= 4;
        for (V$1 = a.current; null !== V$1; ) {
          var f2 = V$1, g2 = f2.child;
          if (0 !== (V$1.flags & 16)) {
            var h = f2.deletions;
            if (null !== h) {
              for (var k2 = 0; k2 < h.length; k2++) {
                var l4 = h[k2];
                for (V$1 = l4; null !== V$1; ) {
                  var m2 = V$1;
                  switch (m2.tag) {
                    case 0:
                    case 11:
                    case 15:
                      Pj(8, m2, f2);
                  }
                  var q2 = m2.child;
                  if (null !== q2) q2.return = m2, V$1 = q2;
                  else for (; null !== V$1; ) {
                    m2 = V$1;
                    var r2 = m2.sibling, y2 = m2.return;
                    Sj(m2);
                    if (m2 === l4) {
                      V$1 = null;
                      break;
                    }
                    if (null !== r2) {
                      r2.return = y2;
                      V$1 = r2;
                      break;
                    }
                    V$1 = y2;
                  }
                }
              }
              var n2 = f2.alternate;
              if (null !== n2) {
                var t2 = n2.child;
                if (null !== t2) {
                  n2.child = null;
                  do {
                    var J2 = t2.sibling;
                    t2.sibling = null;
                    t2 = J2;
                  } while (null !== t2);
                }
              }
              V$1 = f2;
            }
          }
          if (0 !== (f2.subtreeFlags & 2064) && null !== g2) g2.return = f2, V$1 = g2;
          else b: for (; null !== V$1; ) {
            f2 = V$1;
            if (0 !== (f2.flags & 2048)) switch (f2.tag) {
              case 0:
              case 11:
              case 15:
                Pj(9, f2, f2.return);
            }
            var x2 = f2.sibling;
            if (null !== x2) {
              x2.return = f2.return;
              V$1 = x2;
              break b;
            }
            V$1 = f2.return;
          }
        }
        var w2 = a.current;
        for (V$1 = w2; null !== V$1; ) {
          g2 = V$1;
          var u2 = g2.child;
          if (0 !== (g2.subtreeFlags & 2064) && null !== u2) u2.return = g2, V$1 = u2;
          else b: for (g2 = w2; null !== V$1; ) {
            h = V$1;
            if (0 !== (h.flags & 2048)) try {
              switch (h.tag) {
                case 0:
                case 11:
                case 15:
                  Qj(9, h);
              }
            } catch (na) {
              W$1(h, h.return, na);
            }
            if (h === g2) {
              V$1 = null;
              break b;
            }
            var F2 = h.sibling;
            if (null !== F2) {
              F2.return = h.return;
              V$1 = F2;
              break b;
            }
            V$1 = h.return;
          }
        }
        K$1 = e;
        jg();
        if (lc && "function" === typeof lc.onPostCommitFiberRoot) try {
          lc.onPostCommitFiberRoot(kc, a);
        } catch (na) {
        }
        d2 = true;
      }
      return d2;
    } finally {
      C = c, ok.transition = b2;
    }
  }
  return false;
}
function Xk(a, b2, c) {
  b2 = Ji(c, b2);
  b2 = Ni(a, b2, 1);
  a = nh(a, b2, 1);
  b2 = R();
  null !== a && (Ac(a, 1, b2), Dk(a, b2));
}
function W$1(a, b2, c) {
  if (3 === a.tag) Xk(a, a, c);
  else for (; null !== b2; ) {
    if (3 === b2.tag) {
      Xk(b2, a, c);
      break;
    } else if (1 === b2.tag) {
      var d2 = b2.stateNode;
      if ("function" === typeof b2.type.getDerivedStateFromError || "function" === typeof d2.componentDidCatch && (null === Ri || !Ri.has(d2))) {
        a = Ji(c, a);
        a = Qi(b2, a, 1);
        b2 = nh(b2, a, 1);
        a = R();
        null !== b2 && (Ac(b2, 1, a), Dk(b2, a));
        break;
      }
    }
    b2 = b2.return;
  }
}
function Ti(a, b2, c) {
  var d2 = a.pingCache;
  null !== d2 && d2.delete(b2);
  b2 = R();
  a.pingedLanes |= a.suspendedLanes & c;
  Q$1 === a && (Z$1 & c) === c && (4 === T$1 || 3 === T$1 && (Z$1 & 130023424) === Z$1 && 500 > B$1() - fk ? Kk(a, 0) : rk |= c);
  Dk(a, b2);
}
function Yk(a, b2) {
  0 === b2 && (0 === (a.mode & 1) ? b2 = 1 : (b2 = sc, sc <<= 1, 0 === (sc & 130023424) && (sc = 4194304)));
  var c = R();
  a = ih(a, b2);
  null !== a && (Ac(a, b2, c), Dk(a, c));
}
function uj(a) {
  var b2 = a.memoizedState, c = 0;
  null !== b2 && (c = b2.retryLane);
  Yk(a, c);
}
function bk(a, b2) {
  var c = 0;
  switch (a.tag) {
    case 13:
      var d2 = a.stateNode;
      var e = a.memoizedState;
      null !== e && (c = e.retryLane);
      break;
    case 19:
      d2 = a.stateNode;
      break;
    default:
      throw Error(p(314));
  }
  null !== d2 && d2.delete(b2);
  Yk(a, c);
}
var Vk;
Vk = function(a, b2, c) {
  if (null !== a) if (a.memoizedProps !== b2.pendingProps || Wf.current) dh = true;
  else {
    if (0 === (a.lanes & c) && 0 === (b2.flags & 128)) return dh = false, yj(a, b2, c);
    dh = 0 !== (a.flags & 131072) ? true : false;
  }
  else dh = false, I$1 && 0 !== (b2.flags & 1048576) && ug(b2, ng, b2.index);
  b2.lanes = 0;
  switch (b2.tag) {
    case 2:
      var d2 = b2.type;
      ij(a, b2);
      a = b2.pendingProps;
      var e = Yf(b2, H$1.current);
      ch(b2, c);
      e = Nh(null, b2, d2, a, e, c);
      var f2 = Sh();
      b2.flags |= 1;
      "object" === typeof e && null !== e && "function" === typeof e.render && void 0 === e.$$typeof ? (b2.tag = 1, b2.memoizedState = null, b2.updateQueue = null, Zf(d2) ? (f2 = true, cg(b2)) : f2 = false, b2.memoizedState = null !== e.state && void 0 !== e.state ? e.state : null, kh(b2), e.updater = Ei, b2.stateNode = e, e._reactInternals = b2, Ii(b2, d2, a, c), b2 = jj(null, b2, d2, true, f2, c)) : (b2.tag = 0, I$1 && f2 && vg(b2), Xi(null, b2, e, c), b2 = b2.child);
      return b2;
    case 16:
      d2 = b2.elementType;
      a: {
        ij(a, b2);
        a = b2.pendingProps;
        e = d2._init;
        d2 = e(d2._payload);
        b2.type = d2;
        e = b2.tag = Zk(d2);
        a = Ci(d2, a);
        switch (e) {
          case 0:
            b2 = cj(null, b2, d2, a, c);
            break a;
          case 1:
            b2 = hj(null, b2, d2, a, c);
            break a;
          case 11:
            b2 = Yi(null, b2, d2, a, c);
            break a;
          case 14:
            b2 = $i(null, b2, d2, Ci(d2.type, a), c);
            break a;
        }
        throw Error(p(
          306,
          d2,
          ""
        ));
      }
      return b2;
    case 0:
      return d2 = b2.type, e = b2.pendingProps, e = b2.elementType === d2 ? e : Ci(d2, e), cj(a, b2, d2, e, c);
    case 1:
      return d2 = b2.type, e = b2.pendingProps, e = b2.elementType === d2 ? e : Ci(d2, e), hj(a, b2, d2, e, c);
    case 3:
      a: {
        kj(b2);
        if (null === a) throw Error(p(387));
        d2 = b2.pendingProps;
        f2 = b2.memoizedState;
        e = f2.element;
        lh(a, b2);
        qh(b2, d2, null, c);
        var g2 = b2.memoizedState;
        d2 = g2.element;
        if (f2.isDehydrated) if (f2 = { element: d2, isDehydrated: false, cache: g2.cache, pendingSuspenseBoundaries: g2.pendingSuspenseBoundaries, transitions: g2.transitions }, b2.updateQueue.baseState = f2, b2.memoizedState = f2, b2.flags & 256) {
          e = Ji(Error(p(423)), b2);
          b2 = lj(a, b2, d2, c, e);
          break a;
        } else if (d2 !== e) {
          e = Ji(Error(p(424)), b2);
          b2 = lj(a, b2, d2, c, e);
          break a;
        } else for (yg = Lf(b2.stateNode.containerInfo.firstChild), xg = b2, I$1 = true, zg = null, c = Vg(b2, null, d2, c), b2.child = c; c; ) c.flags = c.flags & -3 | 4096, c = c.sibling;
        else {
          Ig();
          if (d2 === e) {
            b2 = Zi(a, b2, c);
            break a;
          }
          Xi(a, b2, d2, c);
        }
        b2 = b2.child;
      }
      return b2;
    case 5:
      return Ah(b2), null === a && Eg(b2), d2 = b2.type, e = b2.pendingProps, f2 = null !== a ? a.memoizedProps : null, g2 = e.children, Ef(d2, e) ? g2 = null : null !== f2 && Ef(d2, f2) && (b2.flags |= 32), gj(a, b2), Xi(a, b2, g2, c), b2.child;
    case 6:
      return null === a && Eg(b2), null;
    case 13:
      return oj(a, b2, c);
    case 4:
      return yh(b2, b2.stateNode.containerInfo), d2 = b2.pendingProps, null === a ? b2.child = Ug(b2, null, d2, c) : Xi(a, b2, d2, c), b2.child;
    case 11:
      return d2 = b2.type, e = b2.pendingProps, e = b2.elementType === d2 ? e : Ci(d2, e), Yi(a, b2, d2, e, c);
    case 7:
      return Xi(a, b2, b2.pendingProps, c), b2.child;
    case 8:
      return Xi(a, b2, b2.pendingProps.children, c), b2.child;
    case 12:
      return Xi(a, b2, b2.pendingProps.children, c), b2.child;
    case 10:
      a: {
        d2 = b2.type._context;
        e = b2.pendingProps;
        f2 = b2.memoizedProps;
        g2 = e.value;
        G(Wg, d2._currentValue);
        d2._currentValue = g2;
        if (null !== f2) if (He$1(f2.value, g2)) {
          if (f2.children === e.children && !Wf.current) {
            b2 = Zi(a, b2, c);
            break a;
          }
        } else for (f2 = b2.child, null !== f2 && (f2.return = b2); null !== f2; ) {
          var h = f2.dependencies;
          if (null !== h) {
            g2 = f2.child;
            for (var k2 = h.firstContext; null !== k2; ) {
              if (k2.context === d2) {
                if (1 === f2.tag) {
                  k2 = mh(-1, c & -c);
                  k2.tag = 2;
                  var l4 = f2.updateQueue;
                  if (null !== l4) {
                    l4 = l4.shared;
                    var m2 = l4.pending;
                    null === m2 ? k2.next = k2 : (k2.next = m2.next, m2.next = k2);
                    l4.pending = k2;
                  }
                }
                f2.lanes |= c;
                k2 = f2.alternate;
                null !== k2 && (k2.lanes |= c);
                bh(
                  f2.return,
                  c,
                  b2
                );
                h.lanes |= c;
                break;
              }
              k2 = k2.next;
            }
          } else if (10 === f2.tag) g2 = f2.type === b2.type ? null : f2.child;
          else if (18 === f2.tag) {
            g2 = f2.return;
            if (null === g2) throw Error(p(341));
            g2.lanes |= c;
            h = g2.alternate;
            null !== h && (h.lanes |= c);
            bh(g2, c, b2);
            g2 = f2.sibling;
          } else g2 = f2.child;
          if (null !== g2) g2.return = f2;
          else for (g2 = f2; null !== g2; ) {
            if (g2 === b2) {
              g2 = null;
              break;
            }
            f2 = g2.sibling;
            if (null !== f2) {
              f2.return = g2.return;
              g2 = f2;
              break;
            }
            g2 = g2.return;
          }
          f2 = g2;
        }
        Xi(a, b2, e.children, c);
        b2 = b2.child;
      }
      return b2;
    case 9:
      return e = b2.type, d2 = b2.pendingProps.children, ch(b2, c), e = eh(e), d2 = d2(e), b2.flags |= 1, Xi(a, b2, d2, c), b2.child;
    case 14:
      return d2 = b2.type, e = Ci(d2, b2.pendingProps), e = Ci(d2.type, e), $i(a, b2, d2, e, c);
    case 15:
      return bj(a, b2, b2.type, b2.pendingProps, c);
    case 17:
      return d2 = b2.type, e = b2.pendingProps, e = b2.elementType === d2 ? e : Ci(d2, e), ij(a, b2), b2.tag = 1, Zf(d2) ? (a = true, cg(b2)) : a = false, ch(b2, c), Gi(b2, d2, e), Ii(b2, d2, e, c), jj(null, b2, d2, true, a, c);
    case 19:
      return xj(a, b2, c);
    case 22:
      return dj(a, b2, c);
  }
  throw Error(p(156, b2.tag));
};
function Fk(a, b2) {
  return ac(a, b2);
}
function $k(a, b2, c, d2) {
  this.tag = a;
  this.key = c;
  this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null;
  this.index = 0;
  this.ref = null;
  this.pendingProps = b2;
  this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null;
  this.mode = d2;
  this.subtreeFlags = this.flags = 0;
  this.deletions = null;
  this.childLanes = this.lanes = 0;
  this.alternate = null;
}
function Bg(a, b2, c, d2) {
  return new $k(a, b2, c, d2);
}
function aj(a) {
  a = a.prototype;
  return !(!a || !a.isReactComponent);
}
function Zk(a) {
  if ("function" === typeof a) return aj(a) ? 1 : 0;
  if (void 0 !== a && null !== a) {
    a = a.$$typeof;
    if (a === Da) return 11;
    if (a === Ga) return 14;
  }
  return 2;
}
function Pg(a, b2) {
  var c = a.alternate;
  null === c ? (c = Bg(a.tag, b2, a.key, a.mode), c.elementType = a.elementType, c.type = a.type, c.stateNode = a.stateNode, c.alternate = a, a.alternate = c) : (c.pendingProps = b2, c.type = a.type, c.flags = 0, c.subtreeFlags = 0, c.deletions = null);
  c.flags = a.flags & 14680064;
  c.childLanes = a.childLanes;
  c.lanes = a.lanes;
  c.child = a.child;
  c.memoizedProps = a.memoizedProps;
  c.memoizedState = a.memoizedState;
  c.updateQueue = a.updateQueue;
  b2 = a.dependencies;
  c.dependencies = null === b2 ? null : { lanes: b2.lanes, firstContext: b2.firstContext };
  c.sibling = a.sibling;
  c.index = a.index;
  c.ref = a.ref;
  return c;
}
function Rg(a, b2, c, d2, e, f2) {
  var g2 = 2;
  d2 = a;
  if ("function" === typeof a) aj(a) && (g2 = 1);
  else if ("string" === typeof a) g2 = 5;
  else a: switch (a) {
    case ya:
      return Tg(c.children, e, f2, b2);
    case za:
      g2 = 8;
      e |= 8;
      break;
    case Aa:
      return a = Bg(12, c, b2, e | 2), a.elementType = Aa, a.lanes = f2, a;
    case Ea:
      return a = Bg(13, c, b2, e), a.elementType = Ea, a.lanes = f2, a;
    case Fa:
      return a = Bg(19, c, b2, e), a.elementType = Fa, a.lanes = f2, a;
    case Ia:
      return pj(c, e, f2, b2);
    default:
      if ("object" === typeof a && null !== a) switch (a.$$typeof) {
        case Ba:
          g2 = 10;
          break a;
        case Ca:
          g2 = 9;
          break a;
        case Da:
          g2 = 11;
          break a;
        case Ga:
          g2 = 14;
          break a;
        case Ha:
          g2 = 16;
          d2 = null;
          break a;
      }
      throw Error(p(130, null == a ? a : typeof a, ""));
  }
  b2 = Bg(g2, c, b2, e);
  b2.elementType = a;
  b2.type = d2;
  b2.lanes = f2;
  return b2;
}
function Tg(a, b2, c, d2) {
  a = Bg(7, a, d2, b2);
  a.lanes = c;
  return a;
}
function pj(a, b2, c, d2) {
  a = Bg(22, a, d2, b2);
  a.elementType = Ia;
  a.lanes = c;
  a.stateNode = { isHidden: false };
  return a;
}
function Qg(a, b2, c) {
  a = Bg(6, a, null, b2);
  a.lanes = c;
  return a;
}
function Sg(a, b2, c) {
  b2 = Bg(4, null !== a.children ? a.children : [], a.key, b2);
  b2.lanes = c;
  b2.stateNode = { containerInfo: a.containerInfo, pendingChildren: null, implementation: a.implementation };
  return b2;
}
function al(a, b2, c, d2, e) {
  this.tag = b2;
  this.containerInfo = a;
  this.finishedWork = this.pingCache = this.current = this.pendingChildren = null;
  this.timeoutHandle = -1;
  this.callbackNode = this.pendingContext = this.context = null;
  this.callbackPriority = 0;
  this.eventTimes = zc(0);
  this.expirationTimes = zc(-1);
  this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0;
  this.entanglements = zc(0);
  this.identifierPrefix = d2;
  this.onRecoverableError = e;
  this.mutableSourceEagerHydrationData = null;
}
function bl(a, b2, c, d2, e, f2, g2, h, k2) {
  a = new al(a, b2, c, h, k2);
  1 === b2 ? (b2 = 1, true === f2 && (b2 |= 8)) : b2 = 0;
  f2 = Bg(3, null, null, b2);
  a.current = f2;
  f2.stateNode = a;
  f2.memoizedState = { element: d2, isDehydrated: c, cache: null, transitions: null, pendingSuspenseBoundaries: null };
  kh(f2);
  return a;
}
function cl(a, b2, c) {
  var d2 = 3 < arguments.length && void 0 !== arguments[3] ? arguments[3] : null;
  return { $$typeof: wa, key: null == d2 ? null : "" + d2, children: a, containerInfo: b2, implementation: c };
}
function dl(a) {
  if (!a) return Vf;
  a = a._reactInternals;
  a: {
    if (Vb(a) !== a || 1 !== a.tag) throw Error(p(170));
    var b2 = a;
    do {
      switch (b2.tag) {
        case 3:
          b2 = b2.stateNode.context;
          break a;
        case 1:
          if (Zf(b2.type)) {
            b2 = b2.stateNode.__reactInternalMemoizedMergedChildContext;
            break a;
          }
      }
      b2 = b2.return;
    } while (null !== b2);
    throw Error(p(171));
  }
  if (1 === a.tag) {
    var c = a.type;
    if (Zf(c)) return bg(a, c, b2);
  }
  return b2;
}
function el(a, b2, c, d2, e, f2, g2, h, k2) {
  a = bl(c, d2, true, a, e, f2, g2, h, k2);
  a.context = dl(null);
  c = a.current;
  d2 = R();
  e = yi(c);
  f2 = mh(d2, e);
  f2.callback = void 0 !== b2 && null !== b2 ? b2 : null;
  nh(c, f2, e);
  a.current.lanes = e;
  Ac(a, e, d2);
  Dk(a, d2);
  return a;
}
function fl(a, b2, c, d2) {
  var e = b2.current, f2 = R(), g2 = yi(e);
  c = dl(c);
  null === b2.context ? b2.context = c : b2.pendingContext = c;
  b2 = mh(f2, g2);
  b2.payload = { element: a };
  d2 = void 0 === d2 ? null : d2;
  null !== d2 && (b2.callback = d2);
  a = nh(e, b2, g2);
  null !== a && (gi(a, e, g2, f2), oh(a, e, g2));
  return g2;
}
function gl(a) {
  a = a.current;
  if (!a.child) return null;
  switch (a.child.tag) {
    case 5:
      return a.child.stateNode;
    default:
      return a.child.stateNode;
  }
}
function hl(a, b2) {
  a = a.memoizedState;
  if (null !== a && null !== a.dehydrated) {
    var c = a.retryLane;
    a.retryLane = 0 !== c && c < b2 ? c : b2;
  }
}
function il(a, b2) {
  hl(a, b2);
  (a = a.alternate) && hl(a, b2);
}
function jl() {
  return null;
}
var kl = "function" === typeof reportError ? reportError : function(a) {
  console.error(a);
};
function ll(a) {
  this._internalRoot = a;
}
ml.prototype.render = ll.prototype.render = function(a) {
  var b2 = this._internalRoot;
  if (null === b2) throw Error(p(409));
  fl(a, b2, null, null);
};
ml.prototype.unmount = ll.prototype.unmount = function() {
  var a = this._internalRoot;
  if (null !== a) {
    this._internalRoot = null;
    var b2 = a.containerInfo;
    Rk(function() {
      fl(null, a, null, null);
    });
    b2[uf] = null;
  }
};
function ml(a) {
  this._internalRoot = a;
}
ml.prototype.unstable_scheduleHydration = function(a) {
  if (a) {
    var b2 = Hc();
    a = { blockedOn: null, target: a, priority: b2 };
    for (var c = 0; c < Qc.length && 0 !== b2 && b2 < Qc[c].priority; c++) ;
    Qc.splice(c, 0, a);
    0 === c && Vc(a);
  }
};
function nl(a) {
  return !(!a || 1 !== a.nodeType && 9 !== a.nodeType && 11 !== a.nodeType);
}
function ol(a) {
  return !(!a || 1 !== a.nodeType && 9 !== a.nodeType && 11 !== a.nodeType && (8 !== a.nodeType || " react-mount-point-unstable " !== a.nodeValue));
}
function pl() {
}
function ql(a, b2, c, d2, e) {
  if (e) {
    if ("function" === typeof d2) {
      var f2 = d2;
      d2 = function() {
        var a2 = gl(g2);
        f2.call(a2);
      };
    }
    var g2 = el(b2, d2, a, 0, null, false, false, "", pl);
    a._reactRootContainer = g2;
    a[uf] = g2.current;
    sf(8 === a.nodeType ? a.parentNode : a);
    Rk();
    return g2;
  }
  for (; e = a.lastChild; ) a.removeChild(e);
  if ("function" === typeof d2) {
    var h = d2;
    d2 = function() {
      var a2 = gl(k2);
      h.call(a2);
    };
  }
  var k2 = bl(a, 0, false, null, null, false, false, "", pl);
  a._reactRootContainer = k2;
  a[uf] = k2.current;
  sf(8 === a.nodeType ? a.parentNode : a);
  Rk(function() {
    fl(b2, k2, c, d2);
  });
  return k2;
}
function rl(a, b2, c, d2, e) {
  var f2 = c._reactRootContainer;
  if (f2) {
    var g2 = f2;
    if ("function" === typeof e) {
      var h = e;
      e = function() {
        var a2 = gl(g2);
        h.call(a2);
      };
    }
    fl(b2, g2, a, e);
  } else g2 = ql(c, b2, a, e, d2);
  return gl(g2);
}
Ec = function(a) {
  switch (a.tag) {
    case 3:
      var b2 = a.stateNode;
      if (b2.current.memoizedState.isDehydrated) {
        var c = tc(b2.pendingLanes);
        0 !== c && (Cc(b2, c | 1), Dk(b2, B$1()), 0 === (K$1 & 6) && (Gj = B$1() + 500, jg()));
      }
      break;
    case 13:
      Rk(function() {
        var b3 = ih(a, 1);
        if (null !== b3) {
          var c2 = R();
          gi(b3, a, 1, c2);
        }
      }), il(a, 1);
  }
};
Fc = function(a) {
  if (13 === a.tag) {
    var b2 = ih(a, 134217728);
    if (null !== b2) {
      var c = R();
      gi(b2, a, 134217728, c);
    }
    il(a, 134217728);
  }
};
Gc = function(a) {
  if (13 === a.tag) {
    var b2 = yi(a), c = ih(a, b2);
    if (null !== c) {
      var d2 = R();
      gi(c, a, b2, d2);
    }
    il(a, b2);
  }
};
Hc = function() {
  return C;
};
Ic = function(a, b2) {
  var c = C;
  try {
    return C = a, b2();
  } finally {
    C = c;
  }
};
yb = function(a, b2, c) {
  switch (b2) {
    case "input":
      bb(a, c);
      b2 = c.name;
      if ("radio" === c.type && null != b2) {
        for (c = a; c.parentNode; ) c = c.parentNode;
        c = c.querySelectorAll("input[name=" + JSON.stringify("" + b2) + '][type="radio"]');
        for (b2 = 0; b2 < c.length; b2++) {
          var d2 = c[b2];
          if (d2 !== a && d2.form === a.form) {
            var e = Db(d2);
            if (!e) throw Error(p(90));
            Wa(d2);
            bb(d2, e);
          }
        }
      }
      break;
    case "textarea":
      ib(a, c);
      break;
    case "select":
      b2 = c.value, null != b2 && fb(a, !!c.multiple, b2, false);
  }
};
Gb = Qk;
Hb = Rk;
var sl = { usingClientEntryPoint: false, Events: [Cb, ue$1, Db, Eb, Fb, Qk] }, tl = { findFiberByHostInstance: Wc, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" };
var ul = { bundleType: tl.bundleType, version: tl.version, rendererPackageName: tl.rendererPackageName, rendererConfig: tl.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: ua.ReactCurrentDispatcher, findHostInstanceByFiber: function(a) {
  a = Zb(a);
  return null === a ? null : a.stateNode;
}, findFiberByHostInstance: tl.findFiberByHostInstance || jl, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
if ("undefined" !== typeof __REACT_DEVTOOLS_GLOBAL_HOOK__) {
  var vl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
  if (!vl.isDisabled && vl.supportsFiber) try {
    kc = vl.inject(ul), lc = vl;
  } catch (a) {
  }
}
reactDom_production_min.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = sl;
reactDom_production_min.createPortal = function(a, b2) {
  var c = 2 < arguments.length && void 0 !== arguments[2] ? arguments[2] : null;
  if (!nl(b2)) throw Error(p(200));
  return cl(a, b2, null, c);
};
reactDom_production_min.createRoot = function(a, b2) {
  if (!nl(a)) throw Error(p(299));
  var c = false, d2 = "", e = kl;
  null !== b2 && void 0 !== b2 && (true === b2.unstable_strictMode && (c = true), void 0 !== b2.identifierPrefix && (d2 = b2.identifierPrefix), void 0 !== b2.onRecoverableError && (e = b2.onRecoverableError));
  b2 = bl(a, 1, false, null, null, c, false, d2, e);
  a[uf] = b2.current;
  sf(8 === a.nodeType ? a.parentNode : a);
  return new ll(b2);
};
reactDom_production_min.findDOMNode = function(a) {
  if (null == a) return null;
  if (1 === a.nodeType) return a;
  var b2 = a._reactInternals;
  if (void 0 === b2) {
    if ("function" === typeof a.render) throw Error(p(188));
    a = Object.keys(a).join(",");
    throw Error(p(268, a));
  }
  a = Zb(b2);
  a = null === a ? null : a.stateNode;
  return a;
};
reactDom_production_min.flushSync = function(a) {
  return Rk(a);
};
reactDom_production_min.hydrate = function(a, b2, c) {
  if (!ol(b2)) throw Error(p(200));
  return rl(null, a, b2, true, c);
};
reactDom_production_min.hydrateRoot = function(a, b2, c) {
  if (!nl(a)) throw Error(p(405));
  var d2 = null != c && c.hydratedSources || null, e = false, f2 = "", g2 = kl;
  null !== c && void 0 !== c && (true === c.unstable_strictMode && (e = true), void 0 !== c.identifierPrefix && (f2 = c.identifierPrefix), void 0 !== c.onRecoverableError && (g2 = c.onRecoverableError));
  b2 = el(b2, null, a, 1, null != c ? c : null, e, false, f2, g2);
  a[uf] = b2.current;
  sf(a);
  if (d2) for (a = 0; a < d2.length; a++) c = d2[a], e = c._getVersion, e = e(c._source), null == b2.mutableSourceEagerHydrationData ? b2.mutableSourceEagerHydrationData = [c, e] : b2.mutableSourceEagerHydrationData.push(
    c,
    e
  );
  return new ml(b2);
};
reactDom_production_min.render = function(a, b2, c) {
  if (!ol(b2)) throw Error(p(200));
  return rl(null, a, b2, false, c);
};
reactDom_production_min.unmountComponentAtNode = function(a) {
  if (!ol(a)) throw Error(p(40));
  return a._reactRootContainer ? (Rk(function() {
    rl(null, null, a, false, function() {
      a._reactRootContainer = null;
      a[uf] = null;
    });
  }), true) : false;
};
reactDom_production_min.unstable_batchedUpdates = Qk;
reactDom_production_min.unstable_renderSubtreeIntoContainer = function(a, b2, c, d2) {
  if (!ol(c)) throw Error(p(200));
  if (null == a || void 0 === a._reactInternals) throw Error(p(38));
  return rl(a, b2, c, false, d2);
};
reactDom_production_min.version = "18.3.1-next-f1338f8080-20240426";
function checkDCE() {
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ === "undefined" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE !== "function") {
    return;
  }
  try {
    __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(checkDCE);
  } catch (err) {
    console.error(err);
  }
}
{
  checkDCE();
  reactDom.exports = reactDom_production_min;
}
var reactDomExports = reactDom.exports;
var m$1 = reactDomExports;
{
  client.createRoot = m$1.createRoot;
  client.hydrateRoot = m$1.hydrateRoot;
}
const createStoreImpl = (createState) => {
  let state;
  const listeners = /* @__PURE__ */ new Set();
  const setState = (partial, replace) => {
    const nextState = typeof partial === "function" ? partial(state) : partial;
    if (!Object.is(nextState, state)) {
      const previousState = state;
      state = (replace != null ? replace : typeof nextState !== "object" || nextState === null) ? nextState : Object.assign({}, state, nextState);
      listeners.forEach((listener) => listener(state, previousState));
    }
  };
  const getState = () => state;
  const getInitialState = () => initialState;
  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };
  const api = { setState, getState, getInitialState, subscribe };
  const initialState = state = createState(setState, getState, api);
  return api;
};
const createStore = (createState) => createState ? createStoreImpl(createState) : createStoreImpl;
const identity = (arg) => arg;
function useStore(api, selector = identity) {
  const slice = React.useSyncExternalStore(
    api.subscribe,
    React.useCallback(() => selector(api.getState()), [api, selector]),
    React.useCallback(() => selector(api.getInitialState()), [api, selector])
  );
  React.useDebugValue(slice);
  return slice;
}
const createImpl = (createState) => {
  const api = createStore(createState);
  const useBoundStore = (selector) => useStore(api, selector);
  Object.assign(useBoundStore, api);
  return useBoundStore;
};
const create = (createState) => createState ? createImpl(createState) : createImpl;
function generateId$1() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
const STORAGE_KEY$1 = "laap-desktop-sessions";
const defaultSession = {
  id: generateId$1(),
  title: "New Chat",
  createdAt: Date.now(),
  updatedAt: Date.now(),
  messageCount: 0
};
function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY$1);
    return raw ? JSON.parse(raw) : [defaultSession];
  } catch {
    return [defaultSession];
  }
}
function persistSessions(sessions) {
  try {
    localStorage.setItem(STORAGE_KEY$1, JSON.stringify(sessions));
  } catch {
  }
}
const useSessionStore = create((set, get) => ({
  sessions: loadSessions(),
  activeSessionId: loadSessions()[0]?.id ?? null,
  setActiveSession: (id2) => set({ activeSessionId: id2 }),
  createSession: () => {
    const session = {
      id: generateId$1(),
      title: "New Chat",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messageCount: 0
    };
    const sessions = [session, ...get().sessions];
    set({ sessions, activeSessionId: session.id });
    persistSessions(sessions);
    return session.id;
  },
  deleteSession: (id2) => {
    const sessions = get().sessions.filter((s) => s.id !== id2);
    const activeSessionId = get().activeSessionId === id2 ? sessions[0]?.id ?? null : get().activeSessionId;
    set({ sessions, activeSessionId });
    persistSessions(sessions);
  },
  renameSession: (id2, title) => {
    const sessions = get().sessions.map(
      (s) => s.id === id2 ? { ...s, title } : s
    );
    set({ sessions });
    persistSessions(sessions);
  },
  updateSessionActivity: (id2) => {
    const sessions = get().sessions.map(
      (s) => s.id === id2 ? { ...s, updatedAt: Date.now(), messageCount: s.messageCount + 1 } : s
    );
    set({ sessions });
    persistSessions(sessions);
  }
}));
const SessionList = ({ onNewChat }) => {
  const sessions = useSessionStore((s) => s.sessions);
  const activeId = useSessionStore((s) => s.activeSessionId);
  const setActive = useSessionStore((s) => s.setActiveSession);
  const deleteSession = useSessionStore((s) => s.deleteSession);
  useSessionStore((s) => s.renameSession);
  const formatDate = (ts) => {
    const d2 = new Date(ts);
    const now = /* @__PURE__ */ new Date();
    const diff = now.getTime() - d2.getTime();
    if (diff < 864e5) return d2.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    if (diff < 6048e5) return d2.toLocaleDateString([], { weekday: "short" });
    return d2.toLocaleDateString([], { month: "short", day: "numeric" });
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", flexDirection: "column", height: "100%" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { padding: "12px 10px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        onClick: onNewChat,
        style: {
          width: "100%",
          padding: "8px 12px",
          borderRadius: 8,
          border: "1px dashed var(--border-light)",
          backgroundColor: "transparent",
          color: "var(--text-secondary)",
          fontSize: 13,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          transition: "all var(--transition-fast)"
        },
        onMouseOver: (e) => {
          e.currentTarget.style.borderColor = "var(--accent)";
          e.currentTarget.style.color = "var(--accent)";
          e.currentTarget.style.backgroundColor = "var(--accent-dim)";
        },
        onMouseOut: (e) => {
          e.currentTarget.style.borderColor = "var(--border-light)";
          e.currentTarget.style.color = "var(--text-secondary)";
          e.currentTarget.style.backgroundColor = "transparent";
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "14", height: "14", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "12", y1: "5", x2: "12", y2: "19" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "5", y1: "12", x2: "19", y2: "12" })
          ] }),
          "New Chat"
        ]
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flex: 1, overflowY: "auto", padding: "0 6px" }, children: sessions.map((session) => /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        onClick: () => setActive(session.id),
        style: {
          padding: "10px 12px",
          borderRadius: 8,
          marginBottom: 2,
          cursor: "pointer",
          backgroundColor: session.id === activeId ? "var(--bg-active)" : "transparent",
          border: session.id === activeId ? "1px solid var(--border-accent)" : "1px solid transparent",
          transition: "all var(--transition-fast)"
        },
        onMouseOver: (e) => {
          if (session.id !== activeId) {
            e.currentTarget.style.backgroundColor = "var(--bg-hover)";
          }
        },
        onMouseOut: (e) => {
          if (session.id !== activeId) {
            e.currentTarget.style.backgroundColor = "transparent";
          }
        },
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "12", height: "12", viewBox: "0 0 24 24", fill: "none", stroke: "var(--text-muted)", strokeWidth: "2", strokeLinecap: "round", style: { flexShrink: 0 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: 0 }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                style: {
                  fontSize: 13,
                  fontWeight: 500,
                  color: session.id === activeId ? "var(--accent)" : "var(--text-primary)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                },
                title: session.title,
                children: session.title
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: 11, color: "var(--text-muted)", marginTop: 2 }, children: [
              session.messageCount,
              " msgs · ",
              formatDate(session.updatedAt)
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: (e) => {
                e.stopPropagation();
                deleteSession(session.id);
              },
              style: {
                backgroundColor: "transparent",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
                padding: 2,
                borderRadius: 4,
                opacity: 0,
                transition: "opacity var(--transition-fast)",
                flexShrink: 0
              },
              onMouseOver: (e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.color = "var(--error)";
              },
              title: "Delete session",
              children: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "12", height: "12", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", y1: "6", x2: "6", y2: "18" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", y1: "6", x2: "18", y2: "18" })
              ] })
            }
          )
        ] })
      },
      session.id
    )) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: 8, textAlign: "center", fontSize: 10, color: "var(--text-muted)" }, children: [
      sessions.length,
      " conversations"
    ] })
  ] });
};
const Avatar = ({ size = 120, emotion = "neutral", isSpeaking = false, onClick }) => {
  const canvasRef = reactExports.useRef(null);
  const pulseRef = reactExports.useRef(0);
  reactExports.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
    let running = true;
    const draw = () => {
      if (!running) return;
      ctx.clearRect(0, 0, size, size);
      const cx = size / 2;
      const cy = size / 2;
      const r2 = size * 0.42;
      pulseRef.current += 0.02;
      const pulse = isSpeaking ? 0.3 + Math.sin(pulseRef.current * 3) * 0.15 : 0.2 + Math.sin(pulseRef.current * 0.8) * 0.05;
      const gradient = ctx.createRadialGradient(cx, cy, r2 * 0.5, cx, cy, r2 * 1.2);
      gradient.addColorStop(0, `rgba(0,212,170,${pulse * 0.3})`);
      gradient.addColorStop(0.5, `rgba(0,212,170,${pulse * 0.15})`);
      gradient.addColorStop(1, "rgba(0,212,170,0)");
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(cx, cy, r2 * 1.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = `rgba(0,212,170,${0.3 + pulse * 0.3})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, r2 + 4, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = "#16213e";
      ctx.strokeStyle = "rgba(0,212,170,0.5)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, r2, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      const ig2 = ctx.createRadialGradient(cx - r2 * 0.3, cy - r2 * 0.3, 0, cx, cy, r2);
      ig2.addColorStop(0, "rgba(0,212,170,0.1)");
      ig2.addColorStop(1, "rgba(0,212,170,0)");
      ctx.fillStyle = ig2;
      ctx.beginPath();
      ctx.arc(cx, cy, r2, 0, Math.PI * 2);
      ctx.fill();
      const eyeY = cy - r2 * 0.1;
      const eyeSpacing = r2 * 0.25;
      const eyeR = r2 * 0.08;
      ctx.fillStyle = "#00d4aa";
      ctx.beginPath();
      ctx.arc(cx - eyeSpacing, eyeY, eyeR, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + eyeSpacing, eyeY, eyeR, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,0.4)";
      ctx.beginPath();
      ctx.arc(cx - eyeSpacing - eyeR * 0.3, eyeY - eyeR * 0.3, eyeR * 0.4, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + eyeSpacing - eyeR * 0.3, eyeY - eyeR * 0.3, eyeR * 0.4, 0, Math.PI * 2);
      ctx.fill();
      const mouthY = cy + r2 * 0.2;
      ctx.strokeStyle = "#00d4aa";
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      if (emotion === "happy" || isSpeaking) {
        ctx.beginPath();
        ctx.arc(cx, mouthY + 2, r2 * 0.15, 0.1, Math.PI - 0.1);
        ctx.stroke();
      } else if (emotion === "sad") {
        ctx.beginPath();
        ctx.arc(cx, mouthY + 8, r2 * 0.15, Math.PI + 0.1, -0.1);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(cx - r2 * 0.12, mouthY);
        ctx.lineTo(cx + r2 * 0.12, mouthY);
        ctx.stroke();
      }
      if (isSpeaking) {
        ctx.strokeStyle = `rgba(0,212,170,${0.2 + Math.sin(pulseRef.current * 4) * 0.1})`;
        ctx.lineWidth = 1.5;
        for (let i = 1; i <= 2; i++) {
          const waveR = r2 * 0.7 + i * 10 + Math.sin(pulseRef.current * 2 + i) * 3;
          ctx.beginPath();
          ctx.arc(cx, cy, waveR, -0.3, 0.3);
          ctx.stroke();
        }
      }
      pulseRef.current = performance.now() / 1e3;
      requestAnimationFrame(draw);
    };
    draw();
    return () => {
      running = false;
    };
  }, [size, emotion, isSpeaking]);
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "canvas",
    {
      ref: canvasRef,
      onClick,
      style: {
        width: size,
        height: size,
        borderRadius: "50%",
        cursor: onClick ? "pointer" : "default",
        display: "block"
      }
    }
  );
};
const NAV_ITEMS = [
  {
    view: "chat",
    label: "Chat",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" }) })
  },
  {
    view: "dashboard",
    label: "Dashboard",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "3", y: "3", width: "7", height: "7" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "14", y: "3", width: "7", height: "7" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "14", y: "14", width: "7", height: "7" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "3", y: "14", width: "7", height: "7" })
    ] })
  },
  {
    view: "settings",
    label: "Settings",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "3" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" })
    ] })
  }
];
const Layout = ({ children, currentView, onNavigate }) => {
  const [expanded, setExpanded] = reactExports.useState(false);
  const [showSessions, setShowSessions] = reactExports.useState(false);
  const createSession = useSessionStore((s) => s.createSession);
  const handleNewChat = () => {
    createSession();
    onNavigate("chat");
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      style: {
        width: "100vw",
        height: "100vh",
        display: "flex",
        backgroundColor: "var(--bg-primary)",
        color: "var(--text-primary)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              width: 56,
              minWidth: 56,
              backgroundColor: "var(--bg-secondary)",
              borderRight: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "12px 0",
              gap: 4
            },
            onMouseEnter: () => setExpanded(false),
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "div",
                {
                  style: {
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    backgroundColor: "var(--accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 16,
                    boxShadow: "var(--shadow-accent)"
                  },
                  children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: 14, fontWeight: 800, color: "#1a1a2e" }, children: "Ao" })
                }
              ),
              NAV_ITEMS.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  onClick: () => onNavigate(item.view),
                  title: item.label,
                  style: {
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    border: "none",
                    backgroundColor: currentView === item.view ? "var(--bg-active)" : "transparent",
                    color: currentView === item.view ? "var(--accent)" : "var(--text-muted)",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all var(--transition-fast)",
                    position: "relative"
                  },
                  onMouseOver: (e) => {
                    if (currentView !== item.view) {
                      e.currentTarget.style.backgroundColor = "var(--bg-hover)";
                      e.currentTarget.style.color = "var(--text-secondary)";
                    }
                  },
                  onMouseOut: (e) => {
                    if (currentView !== item.view) {
                      e.currentTarget.style.backgroundColor = "transparent";
                      e.currentTarget.style.color = "var(--text-muted)";
                    }
                  },
                  children: item.icon
                },
                item.view
              )),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flex: 1 } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Avatar, { size: 36, emotion: "neutral" })
            ]
          }
        ),
        currentView === "chat" && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            style: {
              width: 240,
              minWidth: 240,
              backgroundColor: "var(--bg-secondary)",
              borderRight: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden"
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsx(SessionList, { onNewChat: handleNewChat })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "main",
          {
            style: {
              flex: 1,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              backgroundColor: "var(--bg-primary)"
            },
            children
          }
        )
      ]
    }
  );
};
const WS_URL = "ws://localhost:8766";
const HTTP_URL = "http://localhost:8081";
let ws = null;
let currentCallbacks = null;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
function connectWS(cb2) {
  currentCallbacks = cb2;
  if (ws?.readyState === WebSocket.OPEN) return;
  if (ws?.readyState === WebSocket.CONNECTING) return;
  try {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      reconnectAttempts = 0;
      currentCallbacks?.onConnected?.();
      ws?.send(JSON.stringify({ type: "status" }));
    };
    ws.onmessage = (e) => {
      try {
        const d2 = JSON.parse(e.data);
        switch (d2.type) {
          case "token":
            currentCallbacks?.onToken?.(d2.text);
            break;
          case "response":
            currentCallbacks?.onResponse?.(d2.text);
            break;
          case "tool_call":
            currentCallbacks?.onToolCall?.(d2.name, d2.args || "");
            break;
          case "tool_result":
            currentCallbacks?.onToolResult?.(d2.name, d2.result || "");
            break;
          case "emotion":
            currentCallbacks?.onEmotion?.(d2.name, d2.intensity);
            break;
          case "vitals":
            currentCallbacks?.onVitals?.(d2.energy, d2.focus, d2.mood);
            break;
          case "error":
            currentCallbacks?.onError?.(d2.message || "Unknown error");
            break;
          case "status":
            break;
        }
      } catch {
      }
    };
    ws.onerror = () => {
      currentCallbacks?.onError?.("WebSocket connection error");
    };
    ws.onclose = () => {
      ws = null;
      currentCallbacks?.onDisconnected?.();
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && currentCallbacks) {
        reconnectAttempts++;
        reconnectTimer = setTimeout(() => connectWS(currentCallbacks), 2e3 * reconnectAttempts);
      }
    };
  } catch {
    currentCallbacks?.onError?.("Failed to create WebSocket connection");
  }
}
function disconnectWS() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = null;
  reconnectAttempts = MAX_RECONNECT_ATTEMPTS;
  if (ws) {
    ws.close();
    ws = null;
  }
  currentCallbacks = null;
}
async function apiGet(path) {
  try {
    const res = await fetch(`${HTTP_URL}${path}`, {
      headers: { "Accept": "application/json" }
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
async function apiPost(path, body) {
  try {
    const res = await fetch(`${HTTP_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
const laap = {
  chat: (text, domain = "general", use_psi = false, cb2) => {
    connectWS(cb2);
    const sendMsg = () => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "chat", text, domain, use_psi }));
      }
    };
    if (ws?.readyState === WebSocket.OPEN) {
      sendMsg();
    } else {
      const check = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          clearInterval(check);
          sendMsg();
        }
      }, 100);
      setTimeout(() => clearInterval(check), 5e3);
    }
  },
  tts: (text) => {
    ws?.send(JSON.stringify({ type: "tts", text: text.slice(0, 500) }));
  },
  // REST API methods
  getAgentState: () => apiGet("/api/agent/state"),
  getCharacter: (name) => apiGet(`/api/character/load?name=${encodeURIComponent(name)}`),
  searchCharacter: (q2) => apiGet(`/api/character/search?q=${encodeURIComponent(q2)}`),
  saveMemory: (character, content) => apiPost("/api/character/memory", { character, content }),
  getHealth: () => apiGet("/api/health"),
  disconnect: () => {
    disconnectWS();
  }
};
function M() {
  return { async: false, breaks: false, extensions: null, gfm: true, hooks: null, pedantic: false, renderer: null, silent: false, tokenizer: null, walkTokens: null };
}
var T = M();
function N(l4) {
  T = l4;
}
var _ = { exec: () => null };
function E(l4) {
  let e = [];
  return (t2) => {
    let n2 = Math.max(0, Math.min(3, t2 - 1)), s = e[n2];
    return s || (s = l4(n2), e[n2] = s), s;
  };
}
function d(l4, e = "") {
  let t2 = typeof l4 == "string" ? l4 : l4.source, n2 = { replace: (s, r2) => {
    let i = typeof r2 == "string" ? r2 : r2.source;
    return i = i.replace(m.caret, "$1"), t2 = t2.replace(s, i), n2;
  }, getRegex: () => new RegExp(t2, e) };
  return n2;
}
var Te = ((l4 = "") => {
  try {
    return !!new RegExp("(?<=1)(?<!1)" + l4);
  } catch {
    return false;
  }
})(), m = { codeRemoveIndent: /^(?: {1,4}| {0,3}\t)/gm, outputLinkReplace: /\\([\[\]])/g, indentCodeCompensation: /^(\s+)(?:```)/, beginningSpace: /^\s+/, endingHash: /#$/, startingSpaceChar: /^ /, endingSpaceChar: / $/, nonSpaceChar: /[^ ]/, newLineCharGlobal: /\n/g, tabCharGlobal: /\t/g, multipleSpaceGlobal: /\s+/g, blankLine: /^[ \t]*$/, doubleBlankLine: /\n[ \t]*\n[ \t]*$/, blockquoteStart: /^ {0,3}>/, blockquoteSetextReplace: /\n {0,3}((?:=+|-+) *)(?=\n|$)/g, blockquoteSetextReplace2: /^ {0,3}>[ \t]?/gm, listReplaceNesting: /^ {1,4}(?=( {4})*[^ ])/g, listIsTask: /^\[[ xX]\] +\S/, listReplaceTask: /^\[[ xX]\] +/, listTaskCheckbox: /\[[ xX]\]/, anyLine: /\n.*\n/, hrefBrackets: /^<(.*)>$/, tableDelimiter: /[:|]/, tableAlignChars: /^\||\| *$/g, tableRowBlankLine: /\n[ \t]*$/, tableAlignRight: /^ *-+: *$/, tableAlignCenter: /^ *:-+: *$/, tableAlignLeft: /^ *:-+ *$/, startATag: /^<a /i, endATag: /^<\/a>/i, startPreScriptTag: /^<(pre|code|kbd|script)(\s|>)/i, endPreScriptTag: /^<\/(pre|code|kbd|script)(\s|>)/i, startAngleBracket: /^</, endAngleBracket: />$/, pedanticHrefTitle: /^([^'"]*[^\s])\s+(['"])(.*)\2/, unicodeAlphaNumeric: /[\p{L}\p{N}]/u, escapeTest: /[&<>"']/, escapeReplace: /[&<>"']/g, escapeTestNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/, escapeReplaceNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/g, caret: /(^|[^\[])\^/g, percentDecode: /%25/g, findPipe: /\|/g, splitPipe: / \|/, slashPipe: /\\\|/g, carriageReturn: /\r\n|\r/g, spaceLine: /^ +$/gm, notSpaceStart: /^\S*/, endingNewline: /\n$/, listItemRegex: (l4) => new RegExp(`^( {0,3}${l4})((?:[	 ][^\\n]*)?(?:\\n|$))`), nextBulletRegex: E((l4) => new RegExp(`^ {0,${l4}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`)), hrRegex: E((l4) => new RegExp(`^ {0,${l4}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`)), fencesBeginRegex: E((l4) => new RegExp(`^ {0,${l4}}(?:\`\`\`|~~~)`)), headingBeginRegex: E((l4) => new RegExp(`^ {0,${l4}}#`)), htmlBeginRegex: E((l4) => new RegExp(`^ {0,${l4}}<(?:[a-z].*>|!--)`, "i")), blockquoteBeginRegex: E((l4) => new RegExp(`^ {0,${l4}}>`)) }, Oe = /^(?:[ \t]*(?:\n|$))+/, we = /^((?: {4}| {0,3}\t)[^\n]+(?:\n(?:[ \t]*(?:\n|$))*)?)+/, ye = /^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/, B = /^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/, Pe = /^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/, j = / {0,3}(?:[*+-]|\d{1,9}[.)])/, oe = /^(?!bull |blockCode|fences|blockquote|heading|html|table)((?:.|\n(?!\s*?\n|bull |blockCode|fences|blockquote|heading|html|table))+?)\n {0,3}(=+|-+) *(?:\n+|$)/, ae = d(oe).replace(/bull/g, j).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/\|table/g, "").getRegex(), Se = d(oe).replace(/bull/g, j).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/table/g, / {0,3}\|?(?:[:\- ]*\|)+[\:\- ]*\n/).getRegex(), F = /^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/, $e = /^[^\n]+/, U = /(?!\s*\])(?:\\[\s\S]|[^\[\]\\])+/, Le = d(/^ {0,3}\[(label)\]: *(?:\n[ \t]*)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n[ \t]*)?| *\n[ \t]*)(title))? *(?:\n+|$)/).replace("label", U).replace("title", /(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex(), _e = d(/^(bull)([ \t][^\n]*?)?(?:\n|$)/).replace(/bull/g, j).getRegex(), H = "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul", K = /<!--(?:-?>|[\s\S]*?(?:-->|$))/, ze = d("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$))", "i").replace("comment", K).replace("tag", H).replace("attribute", / +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(), le = d(F).replace("hr", B).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("|table", "").replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]+[^ \\t\\n]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", H).getRegex(), Me = d(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph", le).getRegex(), W = { blockquote: Me, code: we, def: Le, fences: ye, heading: Pe, hr: B, html: ze, lheading: ae, list: _e, newline: Oe, paragraph: le, table: _, text: $e }, se = d("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr", B).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("blockquote", " {0,3}>").replace("code", "(?: {4}| {0,3}	)[^\\n]").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", H).getRegex(), Ee = { ...W, lheading: Se, table: se, paragraph: d(F).replace("hr", B).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("table", se).replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]+[^ \\t\\n]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", H).getRegex() }, Ie = { ...W, html: d(`^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:"[^"]*"|'[^']*'|\\s[^'"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))`).replace("comment", K).replace(/tag/g, "(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(), def: /^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/, heading: /^(#{1,6})(.*)(?:\n+|$)/, fences: _, lheading: /^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/, paragraph: d(F).replace("hr", B).replace("heading", ` *#{1,6} *[^
]`).replace("lheading", ae).replace("|table", "").replace("blockquote", " {0,3}>").replace("|fences", "").replace("|list", "").replace("|html", "").replace("|tag", "").getRegex() }, Ae = /^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/, Ce = /^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/, ue = /^( {2,}|\\)\n(?!\s*$)/, Be = /^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/, I = /[\p{P}\p{S}]/u, Z = /[\s\p{P}\p{S}]/u, X = /[^\s\p{P}\p{S}]/u, De = d(/^((?![*_])punctSpace)/, "u").replace(/punctSpace/g, Z).getRegex(), pe = /(?!~)[\p{P}\p{S}]/u, qe = /(?!~)[\s\p{P}\p{S}]/u, ve = /(?:[^\s\p{P}\p{S}]|~)/u, He = d(/link|precode-code|html/, "g").replace("link", /\[(?:[^\[\]`]|(?<a>`+)[^`]+\k<a>(?!`))*?\]\((?:\\[\s\S]|[^\\\(\)]|\((?:\\[\s\S]|[^\\\(\)])*\))*\)/).replace("precode-", Te ? "(?<!`)()" : "(^^|[^`])").replace("code", /(?<b>`+)[^`]+\k<b>(?!`)/).replace("html", /<(?! )[^<>]*?>/).getRegex(), ce = /^(?:\*+(?:((?!\*)punct)|([^\s*]))?)|^_+(?:((?!_)punct)|([^\s_]))?/, Ze = d(ce, "u").replace(/punct/g, I).getRegex(), Ge = d(ce, "u").replace(/punct/g, pe).getRegex(), he = "^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)punctSpace(\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|notPunctSpace(\\*+)(?=notPunctSpace)", Ne = d(he, "gu").replace(/notPunctSpace/g, X).replace(/punctSpace/g, Z).replace(/punct/g, I).getRegex(), Qe = d(he, "gu").replace(/notPunctSpace/g, ve).replace(/punctSpace/g, qe).replace(/punct/g, pe).getRegex(), je = d("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)punctSpace(_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)", "gu").replace(/notPunctSpace/g, X).replace(/punctSpace/g, Z).replace(/punct/g, I).getRegex(), Fe = d(/^~~?(?:((?!~)punct)|[^\s~])/, "u").replace(/punct/g, I).getRegex(), Ue = "^[^~]+(?=[^~])|(?!~)punct(~~?)(?=[\\s]|$)|notPunctSpace(~~?)(?!~)(?=punctSpace|$)|(?!~)punctSpace(~~?)(?=notPunctSpace)|[\\s](~~?)(?!~)(?=punct)|(?!~)punct(~~?)(?!~)(?=punct)|notPunctSpace(~~?)(?=notPunctSpace)", Ke = d(Ue, "gu").replace(/notPunctSpace/g, X).replace(/punctSpace/g, Z).replace(/punct/g, I).getRegex(), We = d(/\\(punct)/, "gu").replace(/punct/g, I).getRegex(), Xe = d(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme", /[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email", /[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex(), Je = d(K).replace("(?:-->|$)", "-->").getRegex(), Ve = d("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment", Je).replace("attribute", /\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex(), v = /(?:\[(?:\\[\s\S]|[^\[\]\\])*\]|\\[\s\S]|`+(?!`)[^`]*?`+(?!`)|``+(?=\])|[^\[\]\\`])*?/, Ye = d(/^!?\[(label)\]\(\s*(href)(?:(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)(title))?\s*\)/).replace("label", v).replace("href", /<(?:\\.|[^\n<>\\])+>|[^ \t\n\x00-\x1f]*/).replace("title", /"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex(), ke = d(/^!?\[(label)\]\[(ref)\]/).replace("label", v).replace("ref", U).getRegex(), de = d(/^!?\[(ref)\](?:\[\])?/).replace("ref", U).getRegex(), et = d("reflink|nolink(?!\\()", "g").replace("reflink", ke).replace("nolink", de).getRegex(), ie = /[hH][tT][tT][pP][sS]?|[fF][tT][pP]/, J = { _backpedal: _, anyPunctuation: We, autolink: Xe, blockSkip: He, br: ue, code: Ce, del: _, delLDelim: _, delRDelim: _, emStrongLDelim: Ze, emStrongRDelimAst: Ne, emStrongRDelimUnd: je, escape: Ae, link: Ye, nolink: de, punctuation: De, reflink: ke, reflinkSearch: et, tag: Ve, text: Be, url: _ }, tt = { ...J, link: d(/^!?\[(label)\]\((.*?)\)/).replace("label", v).getRegex(), reflink: d(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label", v).getRegex() }, Q = { ...J, emStrongRDelimAst: Qe, emStrongLDelim: Ge, delLDelim: Fe, delRDelim: Ke, url: d(/^((?:protocol):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/).replace("protocol", ie).replace("email", /[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(), _backpedal: /(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/, del: /^(~~?)(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))\1(?=[^~]|$)/, text: d(/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|protocol:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/).replace("protocol", ie).getRegex() }, nt = { ...Q, br: d(ue).replace("{2,}", "*").getRegex(), text: d(Q.text).replace("\\b_", "\\b_| {2,}\\n").replace(/\{2,\}/g, "*").getRegex() }, D = { normal: W, gfm: Ee, pedantic: Ie }, A = { normal: J, gfm: Q, breaks: nt, pedantic: tt };
var rt = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }, ge = (l4) => rt[l4];
function O(l4, e) {
  if (e) {
    if (m.escapeTest.test(l4)) return l4.replace(m.escapeReplace, ge);
  } else if (m.escapeTestNoEncode.test(l4)) return l4.replace(m.escapeReplaceNoEncode, ge);
  return l4;
}
function V(l4) {
  try {
    l4 = encodeURI(l4).replace(m.percentDecode, "%");
  } catch {
    return null;
  }
  return l4;
}
function Y(l4, e) {
  let t2 = l4.replace(m.findPipe, (r2, i, o) => {
    let u2 = false, a = i;
    for (; --a >= 0 && o[a] === "\\"; ) u2 = !u2;
    return u2 ? "|" : " |";
  }), n2 = t2.split(m.splitPipe), s = 0;
  if (n2[0].trim() || n2.shift(), n2.length > 0 && !n2.at(-1)?.trim() && n2.pop(), e) if (n2.length > e) n2.splice(e);
  else for (; n2.length < e; ) n2.push("");
  for (; s < n2.length; s++) n2[s] = n2[s].trim().replace(m.slashPipe, "|");
  return n2;
}
function $(l4, e, t2) {
  let n2 = l4.length;
  if (n2 === 0) return "";
  let s = 0;
  for (; s < n2; ) {
    let r2 = l4.charAt(n2 - s - 1);
    if (r2 === e && true) s++;
    else break;
  }
  return l4.slice(0, n2 - s);
}
function ee(l4) {
  let e = l4.split(`
`), t2 = e.length - 1;
  for (; t2 >= 0 && m.blankLine.test(e[t2]); ) t2--;
  return e.length - t2 <= 2 ? l4 : e.slice(0, t2 + 1).join(`
`);
}
function fe(l4, e) {
  if (l4.indexOf(e[1]) === -1) return -1;
  let t2 = 0;
  for (let n2 = 0; n2 < l4.length; n2++) if (l4[n2] === "\\") n2++;
  else if (l4[n2] === e[0]) t2++;
  else if (l4[n2] === e[1] && (t2--, t2 < 0)) return n2;
  return t2 > 0 ? -2 : -1;
}
function me(l4, e = 0) {
  let t2 = e, n2 = "";
  for (let s of l4) if (s === "	") {
    let r2 = 4 - t2 % 4;
    n2 += " ".repeat(r2), t2 += r2;
  } else n2 += s, t2++;
  return n2;
}
function xe(l4, e, t2, n2, s) {
  let r2 = e.href, i = e.title || null, o = l4[1].replace(s.other.outputLinkReplace, "$1");
  n2.state.inLink = true;
  let u2 = { type: l4[0].charAt(0) === "!" ? "image" : "link", raw: t2, href: r2, title: i, text: o, tokens: n2.inlineTokens(o) };
  return n2.state.inLink = false, u2;
}
function st(l4, e, t2) {
  let n2 = l4.match(t2.other.indentCodeCompensation);
  if (n2 === null) return e;
  let s = n2[1];
  return e.split(`
`).map((r2) => {
    let i = r2.match(t2.other.beginningSpace);
    if (i === null) return r2;
    let [o] = i;
    return o.length >= s.length ? r2.slice(s.length) : r2;
  }).join(`
`);
}
var w = class {
  options;
  rules;
  lexer;
  constructor(e) {
    this.options = e || T;
  }
  space(e) {
    let t2 = this.rules.block.newline.exec(e);
    if (t2 && t2[0].length > 0) return { type: "space", raw: t2[0] };
  }
  code(e) {
    let t2 = this.rules.block.code.exec(e);
    if (t2) {
      let n2 = this.options.pedantic ? t2[0] : ee(t2[0]), s = n2.replace(this.rules.other.codeRemoveIndent, "");
      return { type: "code", raw: n2, codeBlockStyle: "indented", text: s };
    }
  }
  fences(e) {
    let t2 = this.rules.block.fences.exec(e);
    if (t2) {
      let n2 = t2[0], s = st(n2, t2[3] || "", this.rules);
      return { type: "code", raw: n2, lang: t2[2] ? t2[2].trim().replace(this.rules.inline.anyPunctuation, "$1") : t2[2], text: s };
    }
  }
  heading(e) {
    let t2 = this.rules.block.heading.exec(e);
    if (t2) {
      let n2 = t2[2].trim();
      if (this.rules.other.endingHash.test(n2)) {
        let s = $(n2, "#");
        (this.options.pedantic || !s || this.rules.other.endingSpaceChar.test(s)) && (n2 = s.trim());
      }
      return { type: "heading", raw: $(t2[0], `
`), depth: t2[1].length, text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  hr(e) {
    let t2 = this.rules.block.hr.exec(e);
    if (t2) return { type: "hr", raw: $(t2[0], `
`) };
  }
  blockquote(e) {
    let t2 = this.rules.block.blockquote.exec(e);
    if (t2) {
      let n2 = $(t2[0], `
`).split(`
`), s = "", r2 = "", i = [];
      for (; n2.length > 0; ) {
        let o = false, u2 = [], a;
        for (a = 0; a < n2.length; a++) if (this.rules.other.blockquoteStart.test(n2[a])) u2.push(n2[a]), o = true;
        else if (!o) u2.push(n2[a]);
        else break;
        n2 = n2.slice(a);
        let c = u2.join(`
`), p2 = c.replace(this.rules.other.blockquoteSetextReplace, `
    $1`).replace(this.rules.other.blockquoteSetextReplace2, "");
        s = s ? `${s}
${c}` : c, r2 = r2 ? `${r2}
${p2}` : p2;
        let k2 = this.lexer.state.top;
        if (this.lexer.state.top = true, this.lexer.blockTokens(p2, i, true), this.lexer.state.top = k2, n2.length === 0) break;
        let h = i.at(-1);
        if (h?.type === "code") break;
        if (h?.type === "blockquote") {
          let R2 = h, f2 = R2.raw + `
` + n2.join(`
`), S2 = this.blockquote(f2);
          i[i.length - 1] = S2, s = s.substring(0, s.length - R2.raw.length) + S2.raw, r2 = r2.substring(0, r2.length - R2.text.length) + S2.text;
          break;
        } else if (h?.type === "list") {
          let R2 = h, f2 = R2.raw + `
` + n2.join(`
`), S2 = this.list(f2);
          i[i.length - 1] = S2, s = s.substring(0, s.length - h.raw.length) + S2.raw, r2 = r2.substring(0, r2.length - R2.raw.length) + S2.raw, n2 = f2.substring(i.at(-1).raw.length).split(`
`);
          continue;
        }
      }
      return { type: "blockquote", raw: s, tokens: i, text: r2 };
    }
  }
  list(e) {
    let t2 = this.rules.block.list.exec(e);
    if (t2) {
      let n2 = t2[1].trim(), s = n2.length > 1, r2 = { type: "list", raw: "", ordered: s, start: s ? +n2.slice(0, -1) : "", loose: false, items: [] };
      n2 = s ? `\\d{1,9}\\${n2.slice(-1)}` : `\\${n2}`, this.options.pedantic && (n2 = s ? n2 : "[*+-]");
      let i = this.rules.other.listItemRegex(n2), o = false;
      for (; e; ) {
        let a = false, c = "", p2 = "";
        if (!(t2 = i.exec(e)) || this.rules.block.hr.test(e)) break;
        c = t2[0], e = e.substring(c.length);
        let k2 = me(t2[2].split(`
`, 1)[0], t2[1].length), h = e.split(`
`, 1)[0], R2 = !k2.trim(), f2 = 0;
        if (this.options.pedantic ? (f2 = 2, p2 = k2.trimStart()) : R2 ? f2 = t2[1].length + 1 : (f2 = k2.search(this.rules.other.nonSpaceChar), f2 = f2 > 4 ? 1 : f2, p2 = k2.slice(f2), f2 += t2[1].length), R2 && this.rules.other.blankLine.test(h) && (c += h + `
`, e = e.substring(h.length + 1), a = true), !a) {
          let S2 = this.rules.other.nextBulletRegex(f2), te2 = this.rules.other.hrRegex(f2), ne2 = this.rules.other.fencesBeginRegex(f2), re2 = this.rules.other.headingBeginRegex(f2), be2 = this.rules.other.htmlBeginRegex(f2), Re2 = this.rules.other.blockquoteBeginRegex(f2);
          for (; e; ) {
            let G2 = e.split(`
`, 1)[0], C2;
            if (h = G2, this.options.pedantic ? (h = h.replace(this.rules.other.listReplaceNesting, "  "), C2 = h) : C2 = h.replace(this.rules.other.tabCharGlobal, "    "), ne2.test(h) || re2.test(h) || be2.test(h) || Re2.test(h) || S2.test(h) || te2.test(h)) break;
            if (C2.search(this.rules.other.nonSpaceChar) >= f2 || !h.trim()) p2 += `
` + C2.slice(f2);
            else {
              if (R2 || k2.replace(this.rules.other.tabCharGlobal, "    ").search(this.rules.other.nonSpaceChar) >= 4 || ne2.test(k2) || re2.test(k2) || te2.test(k2)) break;
              p2 += `
` + h;
            }
            R2 = !h.trim(), c += G2 + `
`, e = e.substring(G2.length + 1), k2 = C2.slice(f2);
          }
        }
        r2.loose || (o ? r2.loose = true : this.rules.other.doubleBlankLine.test(c) && (o = true)), r2.items.push({ type: "list_item", raw: c, task: !!this.options.gfm && this.rules.other.listIsTask.test(p2), loose: false, text: p2, tokens: [] }), r2.raw += c;
      }
      let u2 = r2.items.at(-1);
      if (u2) u2.raw = u2.raw.trimEnd(), u2.text = u2.text.trimEnd();
      else return;
      r2.raw = r2.raw.trimEnd();
      for (let a of r2.items) {
        this.lexer.state.top = false, a.tokens = this.lexer.blockTokens(a.text, []);
        let c = a.tokens[0];
        if (a.task && (c?.type === "text" || c?.type === "paragraph")) {
          a.text = a.text.replace(this.rules.other.listReplaceTask, ""), c.raw = c.raw.replace(this.rules.other.listReplaceTask, ""), c.text = c.text.replace(this.rules.other.listReplaceTask, "");
          for (let k2 = this.lexer.inlineQueue.length - 1; k2 >= 0; k2--) if (this.rules.other.listIsTask.test(this.lexer.inlineQueue[k2].src)) {
            this.lexer.inlineQueue[k2].src = this.lexer.inlineQueue[k2].src.replace(this.rules.other.listReplaceTask, "");
            break;
          }
          let p2 = this.rules.other.listTaskCheckbox.exec(a.raw);
          if (p2) {
            let k2 = { type: "checkbox", raw: p2[0] + " ", checked: p2[0] !== "[ ]" };
            a.checked = k2.checked, r2.loose ? a.tokens[0] && ["paragraph", "text"].includes(a.tokens[0].type) && "tokens" in a.tokens[0] && a.tokens[0].tokens ? (a.tokens[0].raw = k2.raw + a.tokens[0].raw, a.tokens[0].text = k2.raw + a.tokens[0].text, a.tokens[0].tokens.unshift(k2)) : a.tokens.unshift({ type: "paragraph", raw: k2.raw, text: k2.raw, tokens: [k2] }) : a.tokens.unshift(k2);
          }
        } else a.task && (a.task = false);
        if (!r2.loose) {
          let p2 = a.tokens.filter((h) => h.type === "space"), k2 = p2.length > 0 && p2.some((h) => this.rules.other.anyLine.test(h.raw));
          r2.loose = k2;
        }
      }
      if (r2.loose) for (let a of r2.items) {
        a.loose = true;
        for (let c of a.tokens) c.type === "text" && (c.type = "paragraph");
      }
      return r2;
    }
  }
  html(e) {
    let t2 = this.rules.block.html.exec(e);
    if (t2) {
      let n2 = ee(t2[0]);
      return { type: "html", block: true, raw: n2, pre: t2[1] === "pre" || t2[1] === "script" || t2[1] === "style", text: n2 };
    }
  }
  def(e) {
    let t2 = this.rules.block.def.exec(e);
    if (t2) {
      let n2 = t2[1].toLowerCase().replace(this.rules.other.multipleSpaceGlobal, " "), s = t2[2] ? t2[2].replace(this.rules.other.hrefBrackets, "$1").replace(this.rules.inline.anyPunctuation, "$1") : "", r2 = t2[3] ? t2[3].substring(1, t2[3].length - 1).replace(this.rules.inline.anyPunctuation, "$1") : t2[3];
      return { type: "def", tag: n2, raw: $(t2[0], `
`), href: s, title: r2 };
    }
  }
  table(e) {
    let t2 = this.rules.block.table.exec(e);
    if (!t2 || !this.rules.other.tableDelimiter.test(t2[2])) return;
    let n2 = Y(t2[1]), s = t2[2].replace(this.rules.other.tableAlignChars, "").split("|"), r2 = t2[3]?.trim() ? t2[3].replace(this.rules.other.tableRowBlankLine, "").split(`
`) : [], i = { type: "table", raw: $(t2[0], `
`), header: [], align: [], rows: [] };
    if (n2.length === s.length) {
      for (let o of s) this.rules.other.tableAlignRight.test(o) ? i.align.push("right") : this.rules.other.tableAlignCenter.test(o) ? i.align.push("center") : this.rules.other.tableAlignLeft.test(o) ? i.align.push("left") : i.align.push(null);
      for (let o = 0; o < n2.length; o++) i.header.push({ text: n2[o], tokens: this.lexer.inline(n2[o]), header: true, align: i.align[o] });
      for (let o of r2) i.rows.push(Y(o, i.header.length).map((u2, a) => ({ text: u2, tokens: this.lexer.inline(u2), header: false, align: i.align[a] })));
      return i;
    }
  }
  lheading(e) {
    let t2 = this.rules.block.lheading.exec(e);
    if (t2) {
      let n2 = t2[1].trim();
      return { type: "heading", raw: $(t2[0], `
`), depth: t2[2].charAt(0) === "=" ? 1 : 2, text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  paragraph(e) {
    let t2 = this.rules.block.paragraph.exec(e);
    if (t2) {
      let n2 = t2[1].charAt(t2[1].length - 1) === `
` ? t2[1].slice(0, -1) : t2[1];
      return { type: "paragraph", raw: t2[0], text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  text(e) {
    let t2 = this.rules.block.text.exec(e);
    if (t2) return { type: "text", raw: t2[0], text: t2[0], tokens: this.lexer.inline(t2[0]) };
  }
  escape(e) {
    let t2 = this.rules.inline.escape.exec(e);
    if (t2) return { type: "escape", raw: t2[0], text: t2[1] };
  }
  tag(e) {
    let t2 = this.rules.inline.tag.exec(e);
    if (t2) return !this.lexer.state.inLink && this.rules.other.startATag.test(t2[0]) ? this.lexer.state.inLink = true : this.lexer.state.inLink && this.rules.other.endATag.test(t2[0]) && (this.lexer.state.inLink = false), !this.lexer.state.inRawBlock && this.rules.other.startPreScriptTag.test(t2[0]) ? this.lexer.state.inRawBlock = true : this.lexer.state.inRawBlock && this.rules.other.endPreScriptTag.test(t2[0]) && (this.lexer.state.inRawBlock = false), { type: "html", raw: t2[0], inLink: this.lexer.state.inLink, inRawBlock: this.lexer.state.inRawBlock, block: false, text: t2[0] };
  }
  link(e) {
    let t2 = this.rules.inline.link.exec(e);
    if (t2) {
      let n2 = t2[2].trim();
      if (!this.options.pedantic && this.rules.other.startAngleBracket.test(n2)) {
        if (!this.rules.other.endAngleBracket.test(n2)) return;
        let i = $(n2.slice(0, -1), "\\");
        if ((n2.length - i.length) % 2 === 0) return;
      } else {
        let i = fe(t2[2], "()");
        if (i === -2) return;
        if (i > -1) {
          let u2 = (t2[0].indexOf("!") === 0 ? 5 : 4) + t2[1].length + i;
          t2[2] = t2[2].substring(0, i), t2[0] = t2[0].substring(0, u2).trim(), t2[3] = "";
        }
      }
      let s = t2[2], r2 = "";
      if (this.options.pedantic) {
        let i = this.rules.other.pedanticHrefTitle.exec(s);
        i && (s = i[1], r2 = i[3]);
      } else r2 = t2[3] ? t2[3].slice(1, -1) : "";
      return s = s.trim(), this.rules.other.startAngleBracket.test(s) && (this.options.pedantic && !this.rules.other.endAngleBracket.test(n2) ? s = s.slice(1) : s = s.slice(1, -1)), xe(t2, { href: s && s.replace(this.rules.inline.anyPunctuation, "$1"), title: r2 && r2.replace(this.rules.inline.anyPunctuation, "$1") }, t2[0], this.lexer, this.rules);
    }
  }
  reflink(e, t2) {
    let n2;
    if ((n2 = this.rules.inline.reflink.exec(e)) || (n2 = this.rules.inline.nolink.exec(e))) {
      let s = (n2[2] || n2[1]).replace(this.rules.other.multipleSpaceGlobal, " "), r2 = t2[s.toLowerCase()];
      if (!r2) {
        let i = n2[0].charAt(0);
        return { type: "text", raw: i, text: i };
      }
      return xe(n2, r2, n2[0], this.lexer, this.rules);
    }
  }
  emStrong(e, t2, n2 = "") {
    let s = this.rules.inline.emStrongLDelim.exec(e);
    if (!s || !s[1] && !s[2] && !s[3] && !s[4] || s[4] && n2.match(this.rules.other.unicodeAlphaNumeric)) return;
    if (!(s[1] || s[3] || "") || !n2 || this.rules.inline.punctuation.exec(n2)) {
      let i = [...s[0]].length - 1, o, u2, a = i, c = 0, p2 = s[0][0] === "*" ? this.rules.inline.emStrongRDelimAst : this.rules.inline.emStrongRDelimUnd;
      for (p2.lastIndex = 0, t2 = t2.slice(-1 * e.length + i); (s = p2.exec(t2)) !== null; ) {
        if (o = s[1] || s[2] || s[3] || s[4] || s[5] || s[6], !o) continue;
        if (u2 = [...o].length, s[3] || s[4]) {
          a += u2;
          continue;
        } else if ((s[5] || s[6]) && i % 3 && !((i + u2) % 3)) {
          c += u2;
          continue;
        }
        if (a -= u2, a > 0) continue;
        u2 = Math.min(u2, u2 + a + c);
        let k2 = [...s[0]][0].length, h = e.slice(0, i + s.index + k2 + u2);
        if (Math.min(i, u2) % 2) {
          let f2 = h.slice(1, -1);
          return { type: "em", raw: h, text: f2, tokens: this.lexer.inlineTokens(f2) };
        }
        let R2 = h.slice(2, -2);
        return { type: "strong", raw: h, text: R2, tokens: this.lexer.inlineTokens(R2) };
      }
    }
  }
  codespan(e) {
    let t2 = this.rules.inline.code.exec(e);
    if (t2) {
      let n2 = t2[2].replace(this.rules.other.newLineCharGlobal, " "), s = this.rules.other.nonSpaceChar.test(n2), r2 = this.rules.other.startingSpaceChar.test(n2) && this.rules.other.endingSpaceChar.test(n2);
      return s && r2 && (n2 = n2.substring(1, n2.length - 1)), { type: "codespan", raw: t2[0], text: n2 };
    }
  }
  br(e) {
    let t2 = this.rules.inline.br.exec(e);
    if (t2) return { type: "br", raw: t2[0] };
  }
  del(e, t2, n2 = "") {
    let s = this.rules.inline.delLDelim.exec(e);
    if (!s) return;
    if (!(s[1] || "") || !n2 || this.rules.inline.punctuation.exec(n2)) {
      let i = [...s[0]].length - 1, o, u2, a = i, c = this.rules.inline.delRDelim;
      for (c.lastIndex = 0, t2 = t2.slice(-1 * e.length + i); (s = c.exec(t2)) !== null; ) {
        if (o = s[1] || s[2] || s[3] || s[4] || s[5] || s[6], !o || (u2 = [...o].length, u2 !== i)) continue;
        if (s[3] || s[4]) {
          a += u2;
          continue;
        }
        if (a -= u2, a > 0) continue;
        u2 = Math.min(u2, u2 + a);
        let p2 = [...s[0]][0].length, k2 = e.slice(0, i + s.index + p2 + u2), h = k2.slice(i, -i);
        return { type: "del", raw: k2, text: h, tokens: this.lexer.inlineTokens(h) };
      }
    }
  }
  autolink(e) {
    let t2 = this.rules.inline.autolink.exec(e);
    if (t2) {
      let n2, s;
      return t2[2] === "@" ? (n2 = t2[1], s = "mailto:" + n2) : (n2 = t2[1], s = n2), { type: "link", raw: t2[0], text: n2, href: s, tokens: [{ type: "text", raw: n2, text: n2 }] };
    }
  }
  url(e) {
    let t2;
    if (t2 = this.rules.inline.url.exec(e)) {
      let n2, s;
      if (t2[2] === "@") n2 = t2[0], s = "mailto:" + n2;
      else {
        let r2;
        do
          r2 = t2[0], t2[0] = this.rules.inline._backpedal.exec(t2[0])?.[0] ?? "";
        while (r2 !== t2[0]);
        n2 = t2[0], t2[1] === "www." ? s = "http://" + t2[0] : s = t2[0];
      }
      return { type: "link", raw: t2[0], text: n2, href: s, tokens: [{ type: "text", raw: n2, text: n2 }] };
    }
  }
  inlineText(e) {
    let t2 = this.rules.inline.text.exec(e);
    if (t2) {
      let n2 = this.lexer.state.inRawBlock;
      return { type: "text", raw: t2[0], text: t2[0], escaped: n2 };
    }
  }
};
var x = class l2 {
  tokens;
  options;
  state;
  inlineQueue;
  tokenizer;
  constructor(e) {
    this.tokens = [], this.tokens.links = /* @__PURE__ */ Object.create(null), this.options = e || T, this.options.tokenizer = this.options.tokenizer || new w(), this.tokenizer = this.options.tokenizer, this.tokenizer.options = this.options, this.tokenizer.lexer = this, this.inlineQueue = [], this.state = { inLink: false, inRawBlock: false, top: true };
    let t2 = { other: m, block: D.normal, inline: A.normal };
    this.options.pedantic ? (t2.block = D.pedantic, t2.inline = A.pedantic) : this.options.gfm && (t2.block = D.gfm, this.options.breaks ? t2.inline = A.breaks : t2.inline = A.gfm), this.tokenizer.rules = t2;
  }
  static get rules() {
    return { block: D, inline: A };
  }
  static lex(e, t2) {
    return new l2(t2).lex(e);
  }
  static lexInline(e, t2) {
    return new l2(t2).inlineTokens(e);
  }
  lex(e) {
    e = e.replace(m.carriageReturn, `
`), this.blockTokens(e, this.tokens);
    for (let t2 = 0; t2 < this.inlineQueue.length; t2++) {
      let n2 = this.inlineQueue[t2];
      this.inlineTokens(n2.src, n2.tokens);
    }
    return this.inlineQueue = [], this.tokens;
  }
  blockTokens(e, t2 = [], n2 = false) {
    this.tokenizer.lexer = this, this.options.pedantic && (e = e.replace(m.tabCharGlobal, "    ").replace(m.spaceLine, ""));
    let s = 1 / 0;
    for (; e; ) {
      if (e.length < s) s = e.length;
      else {
        this.infiniteLoopError(e.charCodeAt(0));
        break;
      }
      let r2;
      if (this.options.extensions?.block?.some((o) => (r2 = o.call({ lexer: this }, e, t2)) ? (e = e.substring(r2.raw.length), t2.push(r2), true) : false)) continue;
      if (r2 = this.tokenizer.space(e)) {
        e = e.substring(r2.raw.length);
        let o = t2.at(-1);
        r2.raw.length === 1 && o !== void 0 ? o.raw += `
` : t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.code(e)) {
        e = e.substring(r2.raw.length);
        let o = t2.at(-1);
        o?.type === "paragraph" || o?.type === "text" ? (o.raw += (o.raw.endsWith(`
`) ? "" : `
`) + r2.raw, o.text += `
` + r2.text, this.inlineQueue.at(-1).src = o.text) : t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.fences(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.heading(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.hr(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.blockquote(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.list(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.html(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.def(e)) {
        e = e.substring(r2.raw.length);
        let o = t2.at(-1);
        o?.type === "paragraph" || o?.type === "text" ? (o.raw += (o.raw.endsWith(`
`) ? "" : `
`) + r2.raw, o.text += `
` + r2.raw, this.inlineQueue.at(-1).src = o.text) : this.tokens.links[r2.tag] || (this.tokens.links[r2.tag] = { href: r2.href, title: r2.title }, t2.push(r2));
        continue;
      }
      if (r2 = this.tokenizer.table(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      if (r2 = this.tokenizer.lheading(e)) {
        e = e.substring(r2.raw.length), t2.push(r2);
        continue;
      }
      let i = e;
      if (this.options.extensions?.startBlock) {
        let o = 1 / 0, u2 = e.slice(1), a;
        this.options.extensions.startBlock.forEach((c) => {
          a = c.call({ lexer: this }, u2), typeof a == "number" && a >= 0 && (o = Math.min(o, a));
        }), o < 1 / 0 && o >= 0 && (i = e.substring(0, o + 1));
      }
      if (this.state.top && (r2 = this.tokenizer.paragraph(i))) {
        let o = t2.at(-1);
        n2 && o?.type === "paragraph" ? (o.raw += (o.raw.endsWith(`
`) ? "" : `
`) + r2.raw, o.text += `
` + r2.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = o.text) : t2.push(r2), n2 = i.length !== e.length, e = e.substring(r2.raw.length);
        continue;
      }
      if (r2 = this.tokenizer.text(e)) {
        e = e.substring(r2.raw.length);
        let o = t2.at(-1);
        o?.type === "text" ? (o.raw += (o.raw.endsWith(`
`) ? "" : `
`) + r2.raw, o.text += `
` + r2.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = o.text) : t2.push(r2);
        continue;
      }
      if (e) {
        this.infiniteLoopError(e.charCodeAt(0));
        break;
      }
    }
    return this.state.top = true, t2;
  }
  inline(e, t2 = []) {
    return this.inlineQueue.push({ src: e, tokens: t2 }), t2;
  }
  inlineTokens(e, t2 = []) {
    this.tokenizer.lexer = this;
    let n2 = e, s = null;
    if (this.tokens.links) {
      let a = Object.keys(this.tokens.links);
      if (a.length > 0) for (; (s = this.tokenizer.rules.inline.reflinkSearch.exec(n2)) !== null; ) a.includes(s[0].slice(s[0].lastIndexOf("[") + 1, -1)) && (n2 = n2.slice(0, s.index) + "[" + "a".repeat(s[0].length - 2) + "]" + n2.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex));
    }
    for (; (s = this.tokenizer.rules.inline.anyPunctuation.exec(n2)) !== null; ) n2 = n2.slice(0, s.index) + "++" + n2.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);
    let r2;
    for (; (s = this.tokenizer.rules.inline.blockSkip.exec(n2)) !== null; ) r2 = s[2] ? s[2].length : 0, n2 = n2.slice(0, s.index + r2) + "[" + "a".repeat(s[0].length - r2 - 2) + "]" + n2.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);
    n2 = this.options.hooks?.emStrongMask?.call({ lexer: this }, n2) ?? n2;
    let i = false, o = "", u2 = 1 / 0;
    for (; e; ) {
      if (e.length < u2) u2 = e.length;
      else {
        this.infiniteLoopError(e.charCodeAt(0));
        break;
      }
      i || (o = ""), i = false;
      let a;
      if (this.options.extensions?.inline?.some((p2) => (a = p2.call({ lexer: this }, e, t2)) ? (e = e.substring(a.raw.length), t2.push(a), true) : false)) continue;
      if (a = this.tokenizer.escape(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.tag(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.link(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.reflink(e, this.tokens.links)) {
        e = e.substring(a.raw.length);
        let p2 = t2.at(-1);
        a.type === "text" && p2?.type === "text" ? (p2.raw += a.raw, p2.text += a.text) : t2.push(a);
        continue;
      }
      if (a = this.tokenizer.emStrong(e, n2, o)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.codespan(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.br(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.del(e, n2, o)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (a = this.tokenizer.autolink(e)) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      if (!this.state.inLink && (a = this.tokenizer.url(e))) {
        e = e.substring(a.raw.length), t2.push(a);
        continue;
      }
      let c = e;
      if (this.options.extensions?.startInline) {
        let p2 = 1 / 0, k2 = e.slice(1), h;
        this.options.extensions.startInline.forEach((R2) => {
          h = R2.call({ lexer: this }, k2), typeof h == "number" && h >= 0 && (p2 = Math.min(p2, h));
        }), p2 < 1 / 0 && p2 >= 0 && (c = e.substring(0, p2 + 1));
      }
      if (a = this.tokenizer.inlineText(c)) {
        e = e.substring(a.raw.length), a.raw.slice(-1) !== "_" && (o = a.raw.slice(-1)), i = true;
        let p2 = t2.at(-1);
        p2?.type === "text" ? (p2.raw += a.raw, p2.text += a.text) : t2.push(a);
        continue;
      }
      if (e) {
        this.infiniteLoopError(e.charCodeAt(0));
        break;
      }
    }
    return t2;
  }
  infiniteLoopError(e) {
    let t2 = "Infinite loop on byte: " + e;
    if (this.options.silent) console.error(t2);
    else throw new Error(t2);
  }
};
var y = class {
  options;
  parser;
  constructor(e) {
    this.options = e || T;
  }
  space(e) {
    return "";
  }
  code({ text: e, lang: t2, escaped: n2 }) {
    let s = (t2 || "").match(m.notSpaceStart)?.[0], r2 = e.replace(m.endingNewline, "") + `
`;
    return s ? '<pre><code class="language-' + O(s) + '">' + (n2 ? r2 : O(r2, true)) + `</code></pre>
` : "<pre><code>" + (n2 ? r2 : O(r2, true)) + `</code></pre>
`;
  }
  blockquote({ tokens: e }) {
    return `<blockquote>
${this.parser.parse(e)}</blockquote>
`;
  }
  html({ text: e }) {
    return e;
  }
  def(e) {
    return "";
  }
  heading({ tokens: e, depth: t2 }) {
    return `<h${t2}>${this.parser.parseInline(e)}</h${t2}>
`;
  }
  hr(e) {
    return `<hr>
`;
  }
  list(e) {
    let t2 = e.ordered, n2 = e.start, s = "";
    for (let o = 0; o < e.items.length; o++) {
      let u2 = e.items[o];
      s += this.listitem(u2);
    }
    let r2 = t2 ? "ol" : "ul", i = t2 && n2 !== 1 ? ' start="' + n2 + '"' : "";
    return "<" + r2 + i + `>
` + s + "</" + r2 + `>
`;
  }
  listitem(e) {
    return `<li>${this.parser.parse(e.tokens)}</li>
`;
  }
  checkbox({ checked: e }) {
    return "<input " + (e ? 'checked="" ' : "") + 'disabled="" type="checkbox"> ';
  }
  paragraph({ tokens: e }) {
    return `<p>${this.parser.parseInline(e)}</p>
`;
  }
  table(e) {
    let t2 = "", n2 = "";
    for (let r2 = 0; r2 < e.header.length; r2++) n2 += this.tablecell(e.header[r2]);
    t2 += this.tablerow({ text: n2 });
    let s = "";
    for (let r2 = 0; r2 < e.rows.length; r2++) {
      let i = e.rows[r2];
      n2 = "";
      for (let o = 0; o < i.length; o++) n2 += this.tablecell(i[o]);
      s += this.tablerow({ text: n2 });
    }
    return s && (s = `<tbody>${s}</tbody>`), `<table>
<thead>
` + t2 + `</thead>
` + s + `</table>
`;
  }
  tablerow({ text: e }) {
    return `<tr>
${e}</tr>
`;
  }
  tablecell(e) {
    let t2 = this.parser.parseInline(e.tokens), n2 = e.header ? "th" : "td";
    return (e.align ? `<${n2} align="${e.align}">` : `<${n2}>`) + t2 + `</${n2}>
`;
  }
  strong({ tokens: e }) {
    return `<strong>${this.parser.parseInline(e)}</strong>`;
  }
  em({ tokens: e }) {
    return `<em>${this.parser.parseInline(e)}</em>`;
  }
  codespan({ text: e }) {
    return `<code>${O(e, true)}</code>`;
  }
  br(e) {
    return "<br>";
  }
  del({ tokens: e }) {
    return `<del>${this.parser.parseInline(e)}</del>`;
  }
  link({ href: e, title: t2, tokens: n2 }) {
    let s = this.parser.parseInline(n2), r2 = V(e);
    if (r2 === null) return s;
    e = r2;
    let i = '<a href="' + e + '"';
    return t2 && (i += ' title="' + O(t2) + '"'), i += ">" + s + "</a>", i;
  }
  image({ href: e, title: t2, text: n2, tokens: s }) {
    s && (n2 = this.parser.parseInline(s, this.parser.textRenderer));
    let r2 = V(e);
    if (r2 === null) return O(n2);
    e = r2;
    let i = `<img src="${e}" alt="${O(n2)}"`;
    return t2 && (i += ` title="${O(t2)}"`), i += ">", i;
  }
  text(e) {
    return "tokens" in e && e.tokens ? this.parser.parseInline(e.tokens) : "escaped" in e && e.escaped ? e.text : O(e.text);
  }
};
var L = class {
  strong({ text: e }) {
    return e;
  }
  em({ text: e }) {
    return e;
  }
  codespan({ text: e }) {
    return e;
  }
  del({ text: e }) {
    return e;
  }
  html({ text: e }) {
    return e;
  }
  text({ text: e }) {
    return e;
  }
  link({ text: e }) {
    return "" + e;
  }
  image({ text: e }) {
    return "" + e;
  }
  br() {
    return "";
  }
  checkbox({ raw: e }) {
    return e;
  }
};
var b = class l3 {
  options;
  renderer;
  textRenderer;
  constructor(e) {
    this.options = e || T, this.options.renderer = this.options.renderer || new y(), this.renderer = this.options.renderer, this.renderer.options = this.options, this.renderer.parser = this, this.textRenderer = new L();
  }
  static parse(e, t2) {
    return new l3(t2).parse(e);
  }
  static parseInline(e, t2) {
    return new l3(t2).parseInline(e);
  }
  parse(e) {
    this.renderer.parser = this;
    let t2 = "";
    for (let n2 = 0; n2 < e.length; n2++) {
      let s = e[n2];
      if (this.options.extensions?.renderers?.[s.type]) {
        let i = s, o = this.options.extensions.renderers[i.type].call({ parser: this }, i);
        if (o !== false || !["space", "hr", "heading", "code", "table", "blockquote", "list", "html", "def", "paragraph", "text"].includes(i.type)) {
          t2 += o || "";
          continue;
        }
      }
      let r2 = s;
      switch (r2.type) {
        case "space": {
          t2 += this.renderer.space(r2);
          break;
        }
        case "hr": {
          t2 += this.renderer.hr(r2);
          break;
        }
        case "heading": {
          t2 += this.renderer.heading(r2);
          break;
        }
        case "code": {
          t2 += this.renderer.code(r2);
          break;
        }
        case "table": {
          t2 += this.renderer.table(r2);
          break;
        }
        case "blockquote": {
          t2 += this.renderer.blockquote(r2);
          break;
        }
        case "list": {
          t2 += this.renderer.list(r2);
          break;
        }
        case "checkbox": {
          t2 += this.renderer.checkbox(r2);
          break;
        }
        case "html": {
          t2 += this.renderer.html(r2);
          break;
        }
        case "def": {
          t2 += this.renderer.def(r2);
          break;
        }
        case "paragraph": {
          t2 += this.renderer.paragraph(r2);
          break;
        }
        case "text": {
          t2 += this.renderer.text(r2);
          break;
        }
        default: {
          let i = 'Token with "' + r2.type + '" type was not found.';
          if (this.options.silent) return console.error(i), "";
          throw new Error(i);
        }
      }
    }
    return t2;
  }
  parseInline(e, t2 = this.renderer) {
    this.renderer.parser = this;
    let n2 = "";
    for (let s = 0; s < e.length; s++) {
      let r2 = e[s];
      if (this.options.extensions?.renderers?.[r2.type]) {
        let o = this.options.extensions.renderers[r2.type].call({ parser: this }, r2);
        if (o !== false || !["escape", "html", "link", "image", "strong", "em", "codespan", "br", "del", "text"].includes(r2.type)) {
          n2 += o || "";
          continue;
        }
      }
      let i = r2;
      switch (i.type) {
        case "escape": {
          n2 += t2.text(i);
          break;
        }
        case "html": {
          n2 += t2.html(i);
          break;
        }
        case "link": {
          n2 += t2.link(i);
          break;
        }
        case "image": {
          n2 += t2.image(i);
          break;
        }
        case "checkbox": {
          n2 += t2.checkbox(i);
          break;
        }
        case "strong": {
          n2 += t2.strong(i);
          break;
        }
        case "em": {
          n2 += t2.em(i);
          break;
        }
        case "codespan": {
          n2 += t2.codespan(i);
          break;
        }
        case "br": {
          n2 += t2.br(i);
          break;
        }
        case "del": {
          n2 += t2.del(i);
          break;
        }
        case "text": {
          n2 += t2.text(i);
          break;
        }
        default: {
          let o = 'Token with "' + i.type + '" type was not found.';
          if (this.options.silent) return console.error(o), "";
          throw new Error(o);
        }
      }
    }
    return n2;
  }
};
var P = class {
  options;
  block;
  constructor(e) {
    this.options = e || T;
  }
  static passThroughHooks = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens", "emStrongMask"]);
  static passThroughHooksRespectAsync = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens"]);
  preprocess(e) {
    return e;
  }
  postprocess(e) {
    return e;
  }
  processAllTokens(e) {
    return e;
  }
  emStrongMask(e) {
    return e;
  }
  provideLexer(e = this.block) {
    return e ? x.lex : x.lexInline;
  }
  provideParser(e = this.block) {
    return e ? b.parse : b.parseInline;
  }
};
var q = class {
  defaults = M();
  options = this.setOptions;
  parse = this.parseMarkdown(true);
  parseInline = this.parseMarkdown(false);
  Parser = b;
  Renderer = y;
  TextRenderer = L;
  Lexer = x;
  Tokenizer = w;
  Hooks = P;
  constructor(...e) {
    this.use(...e);
  }
  walkTokens(e, t2) {
    let n2 = [];
    for (let s of e) switch (n2 = n2.concat(t2.call(this, s)), s.type) {
      case "table": {
        let r2 = s;
        for (let i of r2.header) n2 = n2.concat(this.walkTokens(i.tokens, t2));
        for (let i of r2.rows) for (let o of i) n2 = n2.concat(this.walkTokens(o.tokens, t2));
        break;
      }
      case "list": {
        let r2 = s;
        n2 = n2.concat(this.walkTokens(r2.items, t2));
        break;
      }
      default: {
        let r2 = s;
        this.defaults.extensions?.childTokens?.[r2.type] ? this.defaults.extensions.childTokens[r2.type].forEach((i) => {
          let o = r2[i].flat(1 / 0);
          n2 = n2.concat(this.walkTokens(o, t2));
        }) : r2.tokens && (n2 = n2.concat(this.walkTokens(r2.tokens, t2)));
      }
    }
    return n2;
  }
  use(...e) {
    let t2 = this.defaults.extensions || { renderers: {}, childTokens: {} };
    return e.forEach((n2) => {
      let s = { ...n2 };
      if (s.async = this.defaults.async || s.async || false, n2.extensions && (n2.extensions.forEach((r2) => {
        if (!r2.name) throw new Error("extension name required");
        if ("renderer" in r2) {
          let i = t2.renderers[r2.name];
          i ? t2.renderers[r2.name] = function(...o) {
            let u2 = r2.renderer.apply(this, o);
            return u2 === false && (u2 = i.apply(this, o)), u2;
          } : t2.renderers[r2.name] = r2.renderer;
        }
        if ("tokenizer" in r2) {
          if (!r2.level || r2.level !== "block" && r2.level !== "inline") throw new Error("extension level must be 'block' or 'inline'");
          let i = t2[r2.level];
          i ? i.unshift(r2.tokenizer) : t2[r2.level] = [r2.tokenizer], r2.start && (r2.level === "block" ? t2.startBlock ? t2.startBlock.push(r2.start) : t2.startBlock = [r2.start] : r2.level === "inline" && (t2.startInline ? t2.startInline.push(r2.start) : t2.startInline = [r2.start]));
        }
        "childTokens" in r2 && r2.childTokens && (t2.childTokens[r2.name] = r2.childTokens);
      }), s.extensions = t2), n2.renderer) {
        let r2 = this.defaults.renderer || new y(this.defaults);
        for (let i in n2.renderer) {
          if (!(i in r2)) throw new Error(`renderer '${i}' does not exist`);
          if (["options", "parser"].includes(i)) continue;
          let o = i, u2 = n2.renderer[o], a = r2[o];
          r2[o] = (...c) => {
            let p2 = u2.apply(r2, c);
            return p2 === false && (p2 = a.apply(r2, c)), p2 || "";
          };
        }
        s.renderer = r2;
      }
      if (n2.tokenizer) {
        let r2 = this.defaults.tokenizer || new w(this.defaults);
        for (let i in n2.tokenizer) {
          if (!(i in r2)) throw new Error(`tokenizer '${i}' does not exist`);
          if (["options", "rules", "lexer"].includes(i)) continue;
          let o = i, u2 = n2.tokenizer[o], a = r2[o];
          r2[o] = (...c) => {
            let p2 = u2.apply(r2, c);
            return p2 === false && (p2 = a.apply(r2, c)), p2;
          };
        }
        s.tokenizer = r2;
      }
      if (n2.hooks) {
        let r2 = this.defaults.hooks || new P();
        for (let i in n2.hooks) {
          if (!(i in r2)) throw new Error(`hook '${i}' does not exist`);
          if (["options", "block"].includes(i)) continue;
          let o = i, u2 = n2.hooks[o], a = r2[o];
          P.passThroughHooks.has(i) ? r2[o] = (c) => {
            if (this.defaults.async && P.passThroughHooksRespectAsync.has(i)) return (async () => {
              let k2 = await u2.call(r2, c);
              return a.call(r2, k2);
            })();
            let p2 = u2.call(r2, c);
            return a.call(r2, p2);
          } : r2[o] = (...c) => {
            if (this.defaults.async) return (async () => {
              let k2 = await u2.apply(r2, c);
              return k2 === false && (k2 = await a.apply(r2, c)), k2;
            })();
            let p2 = u2.apply(r2, c);
            return p2 === false && (p2 = a.apply(r2, c)), p2;
          };
        }
        s.hooks = r2;
      }
      if (n2.walkTokens) {
        let r2 = this.defaults.walkTokens, i = n2.walkTokens;
        s.walkTokens = function(o) {
          let u2 = [];
          return u2.push(i.call(this, o)), r2 && (u2 = u2.concat(r2.call(this, o))), u2;
        };
      }
      this.defaults = { ...this.defaults, ...s };
    }), this;
  }
  setOptions(e) {
    return this.defaults = { ...this.defaults, ...e }, this;
  }
  lexer(e, t2) {
    return x.lex(e, t2 ?? this.defaults);
  }
  parser(e, t2) {
    return b.parse(e, t2 ?? this.defaults);
  }
  parseMarkdown(e) {
    return (n2, s) => {
      let r2 = { ...s }, i = { ...this.defaults, ...r2 }, o = this.onError(!!i.silent, !!i.async);
      if (this.defaults.async === true && r2.async === false) return o(new Error("marked(): The async option was set to true by an extension. Remove async: false from the parse options object to return a Promise."));
      if (typeof n2 > "u" || n2 === null) return o(new Error("marked(): input parameter is undefined or null"));
      if (typeof n2 != "string") return o(new Error("marked(): input parameter is of type " + Object.prototype.toString.call(n2) + ", string expected"));
      if (i.hooks && (i.hooks.options = i, i.hooks.block = e), i.async) return (async () => {
        let u2 = i.hooks ? await i.hooks.preprocess(n2) : n2, c = await (i.hooks ? await i.hooks.provideLexer(e) : e ? x.lex : x.lexInline)(u2, i), p2 = i.hooks ? await i.hooks.processAllTokens(c) : c;
        i.walkTokens && await Promise.all(this.walkTokens(p2, i.walkTokens));
        let h = await (i.hooks ? await i.hooks.provideParser(e) : e ? b.parse : b.parseInline)(p2, i);
        return i.hooks ? await i.hooks.postprocess(h) : h;
      })().catch(o);
      try {
        i.hooks && (n2 = i.hooks.preprocess(n2));
        let a = (i.hooks ? i.hooks.provideLexer(e) : e ? x.lex : x.lexInline)(n2, i);
        i.hooks && (a = i.hooks.processAllTokens(a)), i.walkTokens && this.walkTokens(a, i.walkTokens);
        let p2 = (i.hooks ? i.hooks.provideParser(e) : e ? b.parse : b.parseInline)(a, i);
        return i.hooks && (p2 = i.hooks.postprocess(p2)), p2;
      } catch (u2) {
        return o(u2);
      }
    };
  }
  onError(e, t2) {
    return (n2) => {
      if (n2.message += `
Please report this to https://github.com/markedjs/marked.`, e) {
        let s = "<p>An error occurred:</p><pre>" + O(n2.message + "", true) + "</pre>";
        return t2 ? Promise.resolve(s) : s;
      }
      if (t2) return Promise.reject(n2);
      throw n2;
    };
  }
};
var z = new q();
function g(l4, e) {
  return z.parse(l4, e);
}
g.options = g.setOptions = function(l4) {
  return z.setOptions(l4), g.defaults = z.defaults, N(g.defaults), g;
};
g.getDefaults = M;
g.defaults = T;
g.use = function(...l4) {
  return z.use(...l4), g.defaults = z.defaults, N(g.defaults), g;
};
g.walkTokens = function(l4, e) {
  return z.walkTokens(l4, e);
};
g.parseInline = z.parseInline;
g.Parser = b;
g.parser = b.parse;
g.Renderer = y;
g.TextRenderer = L;
g.Lexer = x;
g.lexer = x.lex;
g.Tokenizer = w;
g.Hooks = P;
g.parse = g;
g.options;
g.setOptions;
g.use;
g.walkTokens;
g.parseInline;
b.parse;
x.lex;
const Markdown = ({ content, className }) => {
  const html = reactExports.useMemo(() => {
    try {
      const result = g.parse(content, { breaks: true, gfm: true });
      return typeof result === "string" ? result : "";
    } catch {
      return content;
    }
  }, [content]);
  const styles = {
    container: {
      lineHeight: 1.6,
      fontSize: 14,
      wordBreak: "break-word"
    },
    codeBlock: {
      backgroundColor: "rgba(0,0,0,0.3)",
      borderRadius: 6,
      padding: "12px 16px",
      margin: "8px 0",
      overflowX: "auto",
      fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
      fontSize: 13,
      border: "1px solid var(--border)"
    },
    inlineCode: {
      backgroundColor: "rgba(0,212,170,0.1)",
      color: "#00d4aa",
      padding: "2px 6px",
      borderRadius: 4,
      fontFamily: "'Fira Code', 'Consolas', monospace",
      fontSize: 13
    },
    table: {
      borderCollapse: "collapse",
      width: "100%",
      margin: "8px 0",
      fontSize: 13
    },
    th: {
      border: "1px solid var(--border)",
      padding: "8px 12px",
      textAlign: "left",
      backgroundColor: "var(--bg-elevated)",
      fontWeight: 600
    },
    td: {
      border: "1px solid var(--border)",
      padding: "8px 12px"
    },
    blockquote: {
      borderLeft: "3px solid var(--accent)",
      padding: "8px 16px",
      margin: "8px 0",
      backgroundColor: "var(--accent-dim)",
      borderRadius: "0 6px 6px 0",
      color: "var(--text-secondary)"
    },
    link: {
      color: "var(--accent)"
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className,
      style: styles.container,
      dangerouslySetInnerHTML: { __html: html },
      onMouseOver: (e) => {
        const target = e.target;
        if (target.tagName === "A") {
          target.style.color = styles.link.color;
          target.style.textDecoration = "none";
          target.addEventListener("mouseenter", () => {
            target.style.textDecoration = "underline";
          });
          target.addEventListener("mouseleave", () => {
            target.style.textDecoration = "none";
          });
        }
        if (target.tagName === "CODE" && !target.closest("pre")) {
          Object.assign(target.style, styles.inlineCode);
        }
        if (target.tagName === "PRE") {
          Object.assign(target.style, styles.codeBlock);
        }
        if (target.tagName === "BLOCKQUOTE") {
          Object.assign(target.style, styles.blockquote);
        }
        if (target.tagName === "TH") {
          Object.assign(target.style, styles.th);
        }
        if (target.tagName === "TD") {
          Object.assign(target.style, styles.td);
        }
        if (target.tagName === "TABLE") {
          Object.assign(target.style, styles.table);
        }
        if (target.tagName === "IMG") {
          target.style.maxWidth = "100%";
          target.style.borderRadius = "8px";
          target.style.margin = "8px 0";
        }
      }
    }
  );
};
const COLORS$2 = {
  toolBg: "rgba(245,158,11,0.08)",
  toolBorder: "rgba(245,158,11,0.2)",
  toolRunning: "#f59e0b",
  toolDone: "#00d4aa",
  toolError: "#ff6b6b"
};
const ToolCallView = ({ message, isStreaming }) => {
  const toolCalls = React.useMemo(() => {
    const events = [];
    if (!message.content) return events;
    const lines = message.content.split("\n");
    for (const line of lines) {
      const tcMatch = line.match(/\[TOOL_CALL\]\s*(\w+)\(([^)]*)\)/);
      const trMatch = line.match(/\[TOOL_RESULT\]\s*(.+)/);
      const teMatch = line.match(/\[TOOL_ERROR\]\s*(.+)/);
      if (tcMatch) {
        events.push({
          name: tcMatch[1],
          args: tcMatch[2],
          status: "running"
        });
      } else if (trMatch && events.length > 0) {
        events[events.length - 1].status = "complete";
        events[events.length - 1].result = trMatch[1].slice(0, 100);
      } else if (teMatch && events.length > 0) {
        events[events.length - 1].status = "error";
        events[events.length - 1].result = teMatch[1].slice(0, 100);
      }
    }
    return events;
  }, [message.content]);
  if (toolCalls.length === 0) return null;
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginBottom: 8, display: "flex", flexDirection: "column", gap: 4 }, children: toolCalls.map((tc2, i) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 10px",
        borderRadius: 6,
        backgroundColor: COLORS$2.toolBg,
        border: `1px solid ${COLORS$2.toolBorder}`,
        fontSize: 12,
        animation: "fadeIn 0.2s ease"
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            style: {
              width: 6,
              height: 6,
              borderRadius: "50%",
              backgroundColor: tc2.status === "running" ? COLORS$2.toolRunning : tc2.status === "complete" ? COLORS$2.toolDone : COLORS$2.toolError,
              animation: tc2.status === "running" ? "pulse 1s ease infinite" : "none",
              flexShrink: 0
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontWeight: 600, color: "var(--text-primary)", fontSize: 12 }, children: tc2.name }),
        tc2.args && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { color: "var(--text-muted)", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }, children: [
          "(",
          tc2.args.slice(0, 40),
          ")"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          marginLeft: "auto",
          fontSize: 11,
          color: tc2.status === "running" ? COLORS$2.toolRunning : tc2.status === "complete" ? COLORS$2.toolDone : COLORS$2.toolError,
          flexShrink: 0
        }, children: tc2.status === "running" ? "running..." : tc2.status === "complete" ? "done" : "error" })
      ]
    },
    i
  )) });
};
const STORAGE_KEY = "laap-desktop-settings";
function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
function saveSettings(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      theme: state.theme,
      domain: state.domain,
      usePSI: state.usePSI,
      ttsEnabled: state.ttsEnabled,
      autoConnect: state.autoConnect
    }));
  } catch {
  }
}
const useSettingsStore = create((set, get) => ({
  ...{
    theme: "dark",
    domain: "general",
    usePSI: false,
    ttsEnabled: false,
    autoConnect: true,
    backendUrl: "http://localhost:8081",
    wsUrl: "ws://localhost:8766"
  },
  ...loadSettings(),
  setTheme: (theme) => {
    set({ theme });
    document.documentElement.setAttribute("data-theme", theme);
    saveSettings(get());
  },
  setDomain: (domain) => {
    set({ domain });
    saveSettings(get());
  },
  setUsePSI: (use) => {
    set({ usePSI: use });
    saveSettings(get());
  },
  setTtsEnabled: (enabled) => {
    set({ ttsEnabled: enabled });
    saveSettings(get());
  },
  setAutoConnect: (auto) => {
    set({ autoConnect: auto });
    saveSettings(get());
  }
}));
const DOMAINS = ["general", "coding", "debugging", "architecture"];
let messageCounter = 0;
function generateId() {
  messageCounter++;
  return `msg_${Date.now()}_${messageCounter}`;
}
const Chat = () => {
  const [messages, setMessages] = reactExports.useState([]);
  const [input, setInput] = reactExports.useState("");
  const [domain, setDomain] = reactExports.useState("general");
  const [loading, setLoading] = reactExports.useState(false);
  const [streamingMsgId, setStreamingMsgId] = reactExports.useState(null);
  const [error, setError] = reactExports.useState(null);
  const [connected, setConnected] = reactExports.useState(false);
  const [emotion, setEmotion] = reactExports.useState("neutral");
  const [isSpeaking, setIsSpeaking] = reactExports.useState(false);
  const messagesEndRef = reactExports.useRef(null);
  const inputRef = reactExports.useRef(null);
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const updateSessionActivity = useSessionStore((s) => s.updateSessionActivity);
  const settings = useSettingsStore();
  const scrollToBottom = reactExports.useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);
  reactExports.useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  reactExports.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + "px";
    }
  }, [input]);
  const handleSend = reactExports.useCallback(() => {
    const text = input.trim();
    if (!text || loading) return;
    const userMsg = {
      id: generateId(),
      role: "user",
      content: text,
      timestamp: Date.now()
    };
    const assistantMsgId = generateId();
    const assistantMsg = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: Date.now()
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setLoading(true);
    setStreamingMsgId(assistantMsgId);
    setError(null);
    setIsSpeaking(false);
    laap.chat(text, domain, settings.usePSI, {
      onToken: (token) => {
        setMessages(
          (prev) => prev.map(
            (m2) => m2.id === assistantMsgId ? { ...m2, content: m2.content + token } : m2
          )
        );
      },
      onResponse: (fullText) => {
        setMessages(
          (prev) => prev.map(
            (m2) => m2.id === assistantMsgId ? { ...m2, content: fullText } : m2
          )
        );
        setLoading(false);
        setStreamingMsgId(null);
        updateSessionActivity(activeSessionId || "");
        if (settings.ttsEnabled && fullText.length < 500) {
          laap.tts(fullText);
          setIsSpeaking(true);
          setTimeout(() => setIsSpeaking(false), fullText.length * 50);
        }
      },
      onToolCall: () => {
        setIsSpeaking(false);
      },
      onEmotion: (name) => {
        setEmotion(name);
      },
      onError: (err) => {
        setMessages(
          (prev) => prev.map(
            (m2) => m2.id === assistantMsgId ? { ...m2, content: `Error: ${err}` } : m2
          )
        );
        setError(err);
        setLoading(false);
        setStreamingMsgId(null);
      },
      onConnected: () => {
        setConnected(true);
        setError(null);
      },
      onDisconnected: () => {
        setConnected(false);
      }
    });
  }, [input, loading, domain, settings.usePSI, settings.ttsEnabled, activeSessionId, updateSessionActivity]);
  const handleKeyDown = reactExports.useCallback(
    (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );
  const handleClearChat = reactExports.useCallback(() => {
    setMessages([]);
    setError(null);
    setLoading(false);
    setStreamingMsgId(null);
    laap.disconnect();
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        style: {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 20px",
          borderBottom: "1px solid var(--border)",
          backgroundColor: "var(--bg-secondary)"
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 14 }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Avatar, { size: 36, emotion, isSpeaking }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 10 }, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "select",
                {
                  value: domain,
                  onChange: (e) => setDomain(e.target.value),
                  disabled: loading,
                  style: {
                    backgroundColor: "var(--input-bg)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    padding: "6px 24px 6px 10px",
                    fontSize: 12,
                    fontWeight: 500,
                    outline: "none",
                    cursor: loading ? "not-allowed" : "pointer",
                    opacity: loading ? 0.5 : 1,
                    appearance: "none",
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238892b0'/%3E%3C/svg%3E")`,
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "right 8px center"
                  },
                  children: DOMAINS.map((d2) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: d2, children: d2.charAt(0).toUpperCase() + d2.slice(1) }, d2))
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 6 }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  backgroundColor: connected ? "var(--online)" : "var(--offline)",
                  transition: "background-color var(--transition-fast)"
                } }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: 11, color: "var(--text-muted)" }, children: connected ? "Connected" : "Disconnected" })
              ] })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                style: { display: "flex", alignItems: "center", gap: 6, cursor: "pointer" },
                onClick: () => settings.setUsePSI(!settings.usePSI),
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
                    width: 32,
                    height: 18,
                    borderRadius: 10,
                    backgroundColor: settings.usePSI ? "var(--accent)" : "var(--text-muted)",
                    position: "relative",
                    transition: "background-color var(--transition-fast)"
                  }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
                    width: 14,
                    height: 14,
                    borderRadius: "50%",
                    backgroundColor: "#fff",
                    position: "absolute",
                    top: 2,
                    left: settings.usePSI ? 16 : 2,
                    transition: "left var(--transition-fast)",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.3)"
                  } }) }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
                    fontSize: 11,
                    fontWeight: 600,
                    color: settings.usePSI ? "var(--accent)" : "var(--text-muted)",
                    transition: "color var(--transition-fast)"
                  }, children: "PSI" })
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: handleClearChat,
                style: {
                  backgroundColor: "transparent",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  color: "var(--text-muted)",
                  fontSize: 12,
                  padding: "6px 12px",
                  cursor: "pointer",
                  transition: "all var(--transition-fast)"
                },
                onMouseOver: (e) => {
                  e.currentTarget.style.borderColor = "var(--error)";
                  e.currentTarget.style.color = "var(--error)";
                },
                onMouseOut: (e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "var(--text-muted)";
                },
                children: "Clear"
              }
            )
          ] })
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        style: {
          flex: 1,
          overflowY: "auto",
          padding: "20px 24px 0",
          display: "flex",
          flexDirection: "column",
          gap: 16
        },
        children: [
          messages.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              style: {
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-muted)",
                gap: 16
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(Avatar, { size: 80, emotion: "neutral" }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 16, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }, children: "Start a conversation" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 13, color: "var(--text-muted)" }, children: "Type a message to talk to the LAAP agent" })
                ] })
              ]
            }
          ),
          messages.map((msg) => /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                animation: "fadeIn 0.2s ease"
              },
              children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "div",
                {
                  style: {
                    maxWidth: "75%",
                    padding: "10px 16px",
                    borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                    backgroundColor: msg.role === "user" ? "var(--user-bubble)" : "var(--assistant-bubble)",
                    border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                    color: "var(--text-primary)",
                    fontSize: 14,
                    lineHeight: 1.6,
                    wordBreak: "break-word"
                  },
                  children: [
                    msg.role === "assistant" && /* @__PURE__ */ jsxRuntimeExports.jsx(ToolCallView, { message: msg, isStreaming: msg.id === streamingMsgId }),
                    msg.role === "assistant" && msg.content === "" && loading ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: 4, padding: "4px 0" }, children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "typing-dot", style: { width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--accent)", animation: "bounce 1.2s ease infinite" } }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "typing-dot", style: { width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--accent)", animation: "bounce 1.2s ease infinite 0.2s" } }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "typing-dot", style: { width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--accent)", animation: "bounce 1.2s ease infinite 0.4s" } })
                    ] }) : msg.role === "assistant" ? /* @__PURE__ */ jsxRuntimeExports.jsx(Markdown, { content: msg.content }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { whiteSpace: "pre-wrap" }, children: msg.content }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginTop: 6,
                      textAlign: "right"
                    }, children: new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) })
                  ]
                }
              )
            },
            msg.id
          )),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { ref: messagesEndRef })
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        style: {
          padding: "12px 20px 20px",
          borderTop: "1px solid var(--border)",
          backgroundColor: "var(--bg-primary)"
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              style: {
                display: "flex",
                gap: 10,
                alignItems: "flex-end",
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: "8px 8px 8px 16px",
                transition: "border-color var(--transition-fast)"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "textarea",
                  {
                    ref: inputRef,
                    value: input,
                    onChange: (e) => setInput(e.target.value),
                    onKeyDown: handleKeyDown,
                    placeholder: loading ? "Waiting..." : "Type a message...",
                    disabled: loading,
                    rows: 1,
                    style: {
                      flex: 1,
                      backgroundColor: "transparent",
                      border: "none",
                      outline: "none",
                      color: "var(--text-primary)",
                      fontSize: 14,
                      fontFamily: "inherit",
                      resize: "none",
                      maxHeight: 120,
                      padding: "6px 0",
                      lineHeight: 1.4
                    }
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    onClick: handleSend,
                    disabled: loading || !input.trim(),
                    style: {
                      backgroundColor: loading || !input.trim() ? "var(--text-muted)" : "var(--accent)",
                      border: "none",
                      borderRadius: 8,
                      width: 36,
                      height: 36,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                      opacity: loading || !input.trim() ? 0.4 : 1,
                      transition: "all var(--transition-fast)",
                      flexShrink: 0
                    },
                    children: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "#fff", strokeWidth: "2.5", strokeLinecap: "round", strokeLinejoin: "round", children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "22", y1: "2", x2: "11", y2: "13" }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("polygon", { points: "22 2 15 22 11 13 2 9 22 2" })
                    ] })
                  }
                )
              ]
            }
          ),
          error && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: 8, fontSize: 12, color: "var(--error)", textAlign: "center" }, children: error })
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx("style", { children: `
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        .typing-dot { display: inline-block; }
        select option { background-color: var(--bg-secondary); color: var(--text-primary); }
        textarea::placeholder { color: var(--text-muted); }
      ` })
  ] });
};
const COLORS$1 = {
  accent: "#00d4aa",
  error: "#ff6b6b"
};
const Settings = () => {
  const settings = useSettingsStore();
  const [saving, setSaving] = React.useState(false);
  const handleReset = () => {
    if (window.confirm("Reset all settings to defaults?")) {
      localStorage.removeItem("laap-desktop-settings");
      window.location.reload();
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: 32, maxWidth: 640, margin: "0 auto", height: "100%", overflowY: "auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { style: { fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }, children: "Settings" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Section, { title: "Appearance", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      SelectRow,
      {
        label: "Theme",
        value: settings.theme,
        options: [
          { value: "dark", label: "Dark" },
          { value: "light", label: "Light" }
        ],
        onChange: (v2) => settings.setTheme(v2)
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Section, { title: "Chat", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        SelectRow,
        {
          label: "Domain",
          value: settings.domain,
          options: [
            { value: "general", label: "General" },
            { value: "coding", label: "Coding" },
            { value: "debugging", label: "Debugging" },
            { value: "architecture", label: "Architecture" }
          ],
          onChange: settings.setDomain
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        ToggleRow,
        {
          label: "PSI Mode",
          desc: "Enable PSI cognitive processing",
          checked: settings.usePSI,
          onChange: settings.setUsePSI
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Section, { title: "Voice & Audio", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      ToggleRow,
      {
        label: "Text-to-Speech",
        desc: "Voice output for agent responses",
        checked: settings.ttsEnabled,
        onChange: settings.setTtsEnabled
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Section, { title: "Connection", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        ToggleRow,
        {
          label: "Auto-connect on start",
          checked: settings.autoConnect,
          onChange: settings.setAutoConnect
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: 12, color: "var(--text-muted)", marginTop: 8 }, children: [
        "Backend: ",
        settings.backendUrl,
        /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
        "WebSocket: ",
        settings.wsUrl
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Section, { title: "About", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { style: { color: COLORS$1.accent }, children: "LAAP Desktop" }),
      " v0.1.0",
      /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
      "Digital Lifeform Client",
      /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
      "Powered by LAAP AGI Framework"
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: 32, paddingTop: 24, borderTop: "1px solid var(--border)" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        onClick: handleReset,
        style: {
          padding: "8px 20px",
          borderRadius: 8,
          border: `1px solid ${COLORS$1.error}`,
          backgroundColor: "transparent",
          color: COLORS$1.error,
          fontSize: 13,
          cursor: "pointer",
          transition: "all var(--transition-fast)"
        },
        onMouseOver: (e) => {
          e.currentTarget.style.backgroundColor = "rgba(255,107,107,0.1)";
        },
        onMouseOut: (e) => {
          e.currentTarget.style.backgroundColor = "transparent";
        },
        children: "Reset All Settings"
      }
    ) })
  ] });
};
const Section = ({ title, children }) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: 24 }, children: [
  /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { style: { fontSize: 13, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }, children: title }),
  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", flexDirection: "column", gap: 8 }, children })
] });
const SelectRow = ({ label, value, options, onChange }) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", backgroundColor: "var(--bg-elevated)", borderRadius: 8 }, children: [
  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: 13, color: "var(--text-primary)" }, children: label }),
  /* @__PURE__ */ jsxRuntimeExports.jsx(
    "select",
    {
      value,
      onChange: (e) => onChange(e.target.value),
      style: {
        backgroundColor: "var(--input-bg)",
        color: "var(--text-primary)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        padding: "6px 24px 6px 10px",
        fontSize: 13,
        outline: "none",
        cursor: "pointer",
        appearance: "none",
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238892b0'/%3E%3C/svg%3E")`,
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 8px center"
      },
      children: options.map((o) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: o.value, children: o.label }, o.value))
    }
  )
] });
const ToggleRow = ({ label, desc, checked, onChange }) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
  "div",
  {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "8px 12px",
      backgroundColor: "var(--bg-elevated)",
      borderRadius: 8,
      cursor: "pointer"
    },
    onClick: () => onChange(!checked),
    children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 13, color: "var(--text-primary)" }, children: label }),
        desc && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 11, color: "var(--text-muted)", marginTop: 2 }, children: desc })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          style: {
            width: 36,
            height: 20,
            borderRadius: 10,
            backgroundColor: checked ? COLORS$1.accent : "var(--text-muted)",
            position: "relative",
            transition: "background-color var(--transition-fast)",
            flexShrink: 0
          },
          children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                width: 16,
                height: 16,
                borderRadius: "50%",
                backgroundColor: "#fff",
                position: "absolute",
                top: 2,
                left: checked ? 18 : 2,
                transition: "left var(--transition-fast)",
                boxShadow: "0 1px 3px rgba(0,0,0,0.3)"
              }
            }
          )
        }
      )
    ]
  }
);
const COLORS = {
  accent: "#00d4aa",
  online: "#00d4aa",
  offline: "#555"
};
const MetricCard = ({ label, value, icon, color }) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
  "div",
  {
    style: {
      backgroundColor: "var(--bg-elevated)",
      borderRadius: 12,
      padding: "16px 20px",
      border: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      gap: 14,
      transition: "all var(--transition-fast)"
    },
    children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: color || COLORS.accent, flexShrink: 0 }, children: icon }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 22, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.2 }, children: value }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: 12, color: "var(--text-muted)", marginTop: 2 }, children: label })
      ] })
    ]
  }
);
const Dashboard = () => {
  const [state, setState] = reactExports.useState(null);
  const [error, setError] = reactExports.useState(null);
  const [refreshing, setRefreshing] = reactExports.useState(false);
  const fetchState = async () => {
    setRefreshing(true);
    try {
      const res = await fetch("http://localhost:8081/api/agent/state");
      const data = await res.json();
      setState(data);
      setError(null);
    } catch (e) {
      setError("Could not connect to backend");
    } finally {
      setRefreshing(false);
    }
  };
  reactExports.useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 5e3);
    return () => clearInterval(interval);
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: 32, height: "100%", overflowY: "auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { style: { fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }, children: "Dashboard" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          onClick: fetchState,
          style: {
            backgroundColor: "transparent",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "6px 14px",
            color: "var(--text-secondary)",
            fontSize: 12,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 6,
            transition: "all var(--transition-fast)"
          },
          onMouseOver: (e) => {
            e.currentTarget.style.borderColor = "var(--accent)";
            e.currentTarget.style.color = "var(--accent)";
          },
          onMouseOut: (e) => {
            e.currentTarget.style.borderColor = "var(--border)";
            e.currentTarget.style.color = "var(--text-secondary)";
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "svg",
              {
                width: "12",
                height: "12",
                viewBox: "0 0 24 24",
                fill: "none",
                stroke: "currentColor",
                strokeWidth: "2",
                strokeLinecap: "round",
                style: { animation: refreshing ? "spin 1s linear infinite" : "none" },
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "23 4 23 10 17 10" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M20.49 15a9 9 0 1 1-2.12-9.36L23 10" })
                ]
              }
            ),
            "Refresh"
          ]
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        style: {
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 16px",
          borderRadius: 8,
          backgroundColor: error ? "rgba(255,107,107,0.08)" : "rgba(0,212,170,0.08)",
          marginBottom: 24,
          fontSize: 13,
          color: error ? "#ff6b6b" : COLORS.accent
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: error ? "#ff6b6b" : COLORS.online,
                flexShrink: 0
              }
            }
          ),
          error || (state?.agent ? "Agent running" : "Agent offline")
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12, marginBottom: 28 }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          label: "Agent Status",
          value: state?.agent ? "Online" : "Offline",
          color: state?.agent ? COLORS.online : COLORS.offline,
          icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "7", r: "4" })
          ] })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          label: "PSI Mode",
          value: state?.psi_available ? "Active" : "Inactive",
          color: state?.psi_available ? COLORS.online : COLORS.offline,
          icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "10" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "6" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "2" })
          ] })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          label: "Modules",
          value: state?.modules ?? "?",
          icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "2", y: "2", width: "8", height: "8", rx: "1" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "14", y: "2", width: "8", height: "8", rx: "1" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "2", y: "14", width: "8", height: "8", rx: "1" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("rect", { x: "14", y: "14", width: "8", height: "8", rx: "1" })
          ] })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          label: "Connection",
          value: error ? "Lost" : "OK",
          color: error ? "#ff6b6b" : COLORS.online,
          icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M5 12h14" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M12 5l7 7-7 7" })
          ] })
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { style: { fontSize: 13, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }, children: "Quick Actions" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", gap: 8, flexWrap: "wrap" }, children: [
      { label: "Open Chat", icon: "💬", action: "chat" },
      { label: "Settings", icon: "⚙", action: "settings" }
    ].map((action) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        style: {
          padding: "12px 18px",
          backgroundColor: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 13,
          color: "var(--text-primary)",
          transition: "all var(--transition-fast)"
        },
        onMouseOver: (e) => {
          e.currentTarget.style.borderColor = "var(--accent)";
          e.currentTarget.style.backgroundColor = "var(--bg-active)";
        },
        onMouseOut: (e) => {
          e.currentTarget.style.borderColor = "var(--border)";
          e.currentTarget.style.backgroundColor = "var(--bg-elevated)";
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: action.icon }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: action.label })
        ]
      },
      action.label
    )) }),
    state?.psi && Object.keys(state.psi).length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginTop: 28 }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { style: { fontSize: 13, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }, children: "PSI State" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { style: {
        backgroundColor: "var(--bg-elevated)",
        padding: 16,
        borderRadius: 8,
        fontSize: 12,
        color: "var(--text-secondary)",
        overflow: "auto",
        maxHeight: 200,
        border: "1px solid var(--border)"
      }, children: JSON.stringify(state.psi, null, 2) })
    ] })
  ] });
};
const App = () => {
  const [currentView, setCurrentView] = reactExports.useState("chat");
  const theme = useSettingsStore((s) => s.theme);
  reactExports.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);
  const renderView = () => {
    switch (currentView) {
      case "dashboard":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(Dashboard, {});
      case "settings":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(Settings, {});
      case "chat":
      default:
        return /* @__PURE__ */ jsxRuntimeExports.jsx(Chat, {});
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(Layout, { currentView, onNavigate: setCurrentView, children: renderView() });
};
client.createRoot(document.getElementById("root")).render(
  /* @__PURE__ */ jsxRuntimeExports.jsx(React.StrictMode, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(App, {}) })
);
