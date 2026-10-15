// Monkey-patch fs.readlink, fs.readlinkSync and fs.promises.readlink for Node.js 24 on Windows
// In Node 24 on Windows, readlink on regular non-symlink files throws EISDIR instead of EINVAL/UNKNOWN.
// Webpack and enhanced-resolve expect EINVAL, ENOENT or UNKNOWN when a path is not a symlink.
const fs = require('fs');

function normalizeError(err) {
  if (err && err.code === 'EISDIR') {
    err.code = 'EINVAL';
  }
  return err;
}

if (fs && fs.readlink) {
  const origReadlink = fs.readlink;
  fs.readlink = function (path, options, callback) {
    const cb = typeof options === 'function' ? options : callback;
    const opts = typeof options === 'function' ? {} : options;
    return origReadlink.call(fs, path, opts, (err, linkString) => {
      if (err) normalizeError(err);
      return cb(err, linkString);
    });
  };
}

if (fs && fs.readlinkSync) {
  const origReadlinkSync = fs.readlinkSync;
  fs.readlinkSync = function (path, options) {
    try {
      return origReadlinkSync.call(fs, path, options);
    } catch (err) {
      normalizeError(err);
      throw err;
    }
  };
}

if (fs && fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = async function (path, options) {
    try {
      return await origPromisesReadlink.call(fs.promises, path, options);
    } catch (err) {
      normalizeError(err);
      throw err;
    }
  };
}
