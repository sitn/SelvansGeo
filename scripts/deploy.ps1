$version = Read-Host "What is the version ?"
$zip_path = Read-Host "Where do I have to create the zip file ?"

$version = $version.replace('.','')

$new_path = $zip_path + "/SelvansGeo_" + $version

$zip_file = $new_path+ ".zip"

new-item $new_path -itemtype directory

$new_path = $new_path + "/SelvansGeo_" + $version

new-item $new_path -itemtype directory

$current_path = Convert-Path .
$current_path = $current_path + "\*"

Copy-Item -Path $current_path -Destination $new_path -Exclude @("__pycache__", "scripts", ".gitgnore", '.git') -Recurse -Force

Compress-Archive -Path $new_path -DestinationPath $zip_file
