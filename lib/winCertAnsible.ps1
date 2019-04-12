$current = Get-Location
$current = $current.Path

$username = $env:USERNAME
$old_certs = Get-ChildItem -Path cert:\LocalMachine\Root | Where-Object { $_.Subject -eq "CN=$username" }

foreach($cert in $old_certs){
    Remove-Item $cert.PSPath
}

$cert = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2
$cert.Import("$current\cert.pem")


$thumbprint = (Get-ChildItem -Path cert:\LocalMachine\Root | Where-Object { $_.Subject -eq "CN=$username" }).Thumbprint

# Ajoute le certificat au store Root

$store_name = [System.Security.Cryptography.X509Certificates.StoreName]::Root
$store_location = [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
$store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
$store.Open("MaxAllowed")
$store.Add($cert)
$store.Close()

# Ajoute le certificat au store TrustedPeople

$store_name = [System.Security.Cryptography.X509Certificates.StoreName]::TrustedPeople
$store_location = [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
$store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
$store.Open("MaxAllowed")
$store.Add($cert)
$store.Close()


$cred = Get-Credential -UserName $username -Message "Nous ne vous le demanderons qu'une fois."
$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $cred.Password

$thumbprint = (Get-ChildItem -Path cert:\LocalMachine\Root | Where-Object { $_.Subject -eq "CN=$username" }).Thumbprint

if($thumbprint.Length -gt 1){
    $old_thumb = $thumbprint[0]
    $old_cert = (Get-ChildItem -Path cert:\LocalMachine\Root | Where-Object { $_.Thumbprint -eq "$old_thumb" }).Thumbprint
    $old_cert.Remove
}

New-Item -Path WSMan:\localhost\ClientCertificate `
    -Subject "$username@localhost" `
    -URI * `
    -Issuer $thumbprint `
    -Credential $credential `
    -Force