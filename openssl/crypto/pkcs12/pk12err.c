/*
 * Generated by util/mkerr.pl DO NOT EDIT
 * Copyright 1995-2023 The OpenSSL Project Authors. All Rights Reserved.
 *
 * Licensed under the Apache License 2.0 (the "License").  You may not use
 * this file except in compliance with the License.  You can obtain a copy
 * in the file LICENSE in the source distribution or at
 * https://www.openssl.org/source/license.html
 */

#include <openssl/err.h>
#include <openssl/pkcs12err.h>
#include "crypto/pkcs12err.h"

#ifndef OPENSSL_NO_ERR

static const ERR_STRING_DATA PKCS12_str_reasons[] = {
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_CALLBACK_FAILED), "callback failed"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_CANT_PACK_STRUCTURE),
    "can't pack structure"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_CONTENT_TYPE_NOT_DATA),
    "content type not data"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_DECODE_ERROR), "decode error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_ENCODE_ERROR), "encode error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_ENCRYPT_ERROR), "encrypt error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_ERROR_SETTING_ENCRYPTED_DATA_TYPE),
    "error setting encrypted data type"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_INVALID_NULL_ARGUMENT),
    "invalid null argument"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_INVALID_NULL_PKCS12_POINTER),
    "invalid null pkcs12 pointer"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_INVALID_TYPE), "invalid type"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_IV_GEN_ERROR), "iv gen error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_KEY_GEN_ERROR), "key gen error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_MAC_ABSENT), "mac absent"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_MAC_GENERATION_ERROR),
    "mac generation error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_MAC_SETUP_ERROR), "mac setup error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_MAC_STRING_SET_ERROR),
    "mac string set error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_MAC_VERIFY_FAILURE),
    "mac verify failure"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_PARSE_ERROR), "parse error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_PKCS12_CIPHERFINAL_ERROR),
    "pkcs12 cipherfinal error"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_UNKNOWN_DIGEST_ALGORITHM),
    "unknown digest algorithm"},
    {ERR_PACK(ERR_LIB_PKCS12, 0, PKCS12_R_UNSUPPORTED_PKCS12_MODE),
    "unsupported pkcs12 mode"},
    {0, NULL}
};

#endif

int ossl_err_load_PKCS12_strings(void)
{
#ifndef OPENSSL_NO_ERR
    if (ERR_reason_error_string(PKCS12_str_reasons[0].error) == NULL)
        ERR_load_strings_const(PKCS12_str_reasons);
#endif
    return 1;
}