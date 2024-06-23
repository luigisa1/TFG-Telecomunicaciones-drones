from Crypto.Cipher import AES
import binascii

def decrypt_message(encrypted_message, key, iv):
    # AES instancia para descifrar el mensaje
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Descifrado del mensaje
    desencriptado = cipher.decrypt(encrypted_message)

    return desencriptado


def desencriptado_limpio(mensaje, key, iv):
    inicio_encrypted_data = mensaje.find('[') + 1
    fin_encrypted_data = mensaje.find('\r')
    encrypted_data = binascii.unhexlify(
        mensaje[inicio_encrypted_data:fin_encrypted_data])

    # print(encrypted_data)
    desencriptado = decrypt_message(
        encrypted_data, key, iv).decode('ascii')

    # print("El mensaje desencriptado es: ", desencriptado)

    # Es necesario retirar el padding
    fin_padding = desencriptado.find('|')+1
    desencriptado = desencriptado[fin_padding:]
    desencriptado += mensaje[fin_encrypted_data]
    # print("El mensajer sin padding es: ", repr(desencriptado))

    mensaje = mensaje[mensaje.find('\n'):mensaje.find(
        '[')+1] + desencriptado

    return mensaje
