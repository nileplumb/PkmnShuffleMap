const fs = require('fs')

module.exports.update = async function update() {
  const checkFolders = async (folder) => {
    folder = folder.replace('//', '/')
    const files = await fs.promises.readdir(folder)
    let newJson = {}
    let hasSubFolders = false

    await Promise.all(files.map(async file => {
      if (!file.includes('.')) {
        hasSubFolders = true
        newJson[file] = await checkFolders(`${folder}/${file}`)
      }
    }))
    if (!hasSubFolders) {
      newJson = files.filter(file => file.includes('.png'))
    }
    fs.writeFileSync(`./${folder === './' ? '' : `${folder}/`}index.json`, JSON.stringify(newJson))
    return newJson
  }
  await checkFolders('./')
}